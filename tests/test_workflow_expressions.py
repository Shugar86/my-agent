"""Tests for the expression engine, retry policy, and new utility nodes.

These cover the n8n-like upgrades:
    - ``core.workflow.expressions``: path access, helpers, list indexing.
    - ``WorkflowExecutor`` retry + error edge routing.
    - ``util.set / util.merge / util.wait / util.code`` handlers.
"""

from __future__ import annotations

import os
import pytest

os.environ.setdefault("ENV", "test")


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Fresh test DB per test (mirrors test_workflow_engine.py setup)."""
    db_path = tmp_path / "test_expressions.db"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from core.db_migrate import run_migrations
    from core.db_manager import DBManager
    import core.db_manager as dm
    dm.db = DBManager(f"sqlite:///{db_path}")
    run_migrations(f"sqlite:///{db_path}")
    yield


class TestExpressionEngine:
    def test_path_access(self):
        from core.workflow.expressions import render_template

        scope = {"trigger": {"payload": {"name": "Alice", "age": 30}}}
        assert render_template("Hello {{ trigger.payload.name }}", scope) == "Hello Alice"

    def test_list_index(self):
        from core.workflow.expressions import render_template

        scope = {"a1": {"items": ["one", "two", "three"]}}
        assert render_template("{{ a1.items[1] }}", scope) == "two"

    def test_helpers_now_and_upper(self):
        from core.workflow.expressions import render_template

        scope = {"trigger": {"name": "alice"}}
        out = render_template("{{ upper(trigger.name) }}", scope)
        assert out == "ALICE"

    def test_default_helper(self):
        from core.workflow.expressions import render_template

        scope = {"trigger": {"name": ""}}
        assert render_template("{{ default(trigger.name, 'guest') }}", scope) == "guest"

    def test_single_expression_returns_native(self):
        from core.workflow.expressions import render_template

        scope = {"a1": {"items": [1, 2, 3]}}
        # When the whole string is a single expression, we keep the native type.
        result = render_template("{{ a1.items }}", scope)
        assert result == [1, 2, 3]

    def test_unknown_helper_keeps_template(self):
        from core.workflow.expressions import render_template

        scope = {}
        # Unknown helper raises during eval; the renderer must not crash and must
        # leave the text untouched (visible to the user as "unresolved").
        out = render_template("{{ doesnotexist() }}", scope)
        assert out == "{{ doesnotexist() }}"

    def test_legacy_pattern_still_works(self):
        from core.workflow.models import RunContext

        ctx = RunContext(run_id="r1", workflow_id="w1")
        ctx.node_outputs["a1"] = {"output": "hello"}
        assert ctx.resolve_template("{{a1.output}}") == "hello"

    def test_resolve_config_recursive(self):
        from core.workflow.models import RunContext

        ctx = RunContext(
            run_id="r1",
            workflow_id="w1",
            trigger_payload={"email": "foo@bar.com"},
        )
        config = {
            "to": "{{ trigger.email }}",
            "headers": {"X-User": "{{ upper(trigger.email) }}"},
            "tags": ["{{ trigger.email }}", "static"],
        }
        resolved = ctx.resolve_config(config)
        assert resolved["to"] == "foo@bar.com"
        assert resolved["headers"]["X-User"] == "FOO@BAR.COM"
        assert resolved["tags"] == ["foo@bar.com", "static"]


class TestRetryAndErrorPath:
    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self):
        from core.workflow.executor import WorkflowExecutor
        from core.workflow.registry import register_node_handler, reset_registry
        from core.workflow.store import WorkflowStore
        import core.workflow.executor as exec_mod

        reset_registry()
        exec_mod._handlers_registered = False

        attempts = {"n": 0}

        async def flaky(ctx, config):
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise RuntimeError("transient")
            return {"output": "ok", "success": True}

        register_node_handler("trigger.webhook", flaky)
        exec_mod._handlers_registered = True

        store = WorkflowStore()
        wf = store.create_workflow("Retry", {
            "nodes": [{"id": "t1", "type": "trigger.webhook", "config": {"retry": {"max_attempts": 3, "backoff_seconds": 0}}}],
            "edges": [],
        })

        executor = WorkflowExecutor(store=store)
        result = await executor.run(wf["id"])
        assert result["success"] is True
        assert attempts["n"] == 2

    @pytest.mark.asyncio
    async def test_error_edge_routes_alternative_path(self):
        from core.workflow.executor import WorkflowExecutor
        from core.workflow.registry import register_node_handler, reset_registry
        from core.workflow.store import WorkflowStore
        import core.workflow.executor as exec_mod

        reset_registry()
        exec_mod._handlers_registered = False

        executed: list[str] = []

        async def trig(ctx, config):
            executed.append("t1")
            return {"output": "ok"}

        async def fails(ctx, config):
            executed.append("x1")
            raise RuntimeError("kaboom")

        async def fallback(ctx, config):
            executed.append("x2")
            return {"output": "fallback"}

        register_node_handler("trigger.webhook", trig)
        register_node_handler("action.slack", fails)
        register_node_handler("action.telegram", fallback)
        exec_mod._handlers_registered = True

        store = WorkflowStore()
        wf = store.create_workflow("ErrorPath", {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "x1", "type": "action.slack", "config": {"continue_on_error": True}},
                {"id": "x2", "type": "action.telegram", "config": {}},
            ],
            "edges": [
                {"from": "t1", "to": "x1"},
                {"from": "x1", "to": "x2", "label": "error"},
            ],
        })

        executor = WorkflowExecutor(store=store)
        result = await executor.run(wf["id"])
        assert result["success"] is True
        assert executed == ["t1", "x1", "x2"]


class TestUtilNodes:
    @pytest.mark.asyncio
    async def test_util_set_and_merge(self):
        from core.workflow.models import RunContext
        from core.workflow.nodes.util import handle_util_set, handle_util_merge

        ctx = RunContext(run_id="r1", workflow_id="w1", trigger_payload={"name": "Alice"})
        out = await handle_util_set(ctx, {"values": {"greeting": "Hi {{ trigger.name }}"}})
        assert out["output"]["greeting"] == "Hi Alice"

        ctx.node_outputs["s1"] = {"output": {"a": 1}}
        ctx.node_outputs["s2"] = {"output": {"b": 2}}
        merged = await handle_util_merge(ctx, {"sources": ["s1", "s2"]})
        assert merged["output"] == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_util_wait_clamped(self):
        from core.workflow.models import RunContext
        from core.workflow.nodes.util import handle_util_wait

        ctx = RunContext(run_id="r1", workflow_id="w1")
        out = await handle_util_wait(ctx, {"seconds": 0.01})
        assert out["success"] is True
        assert out["output"]["waited_seconds"] == 0.01

    @pytest.mark.asyncio
    async def test_util_code_sandbox_blocks_imports(self):
        from core.workflow.models import RunContext
        from core.workflow.nodes.util import handle_util_code

        ctx = RunContext(run_id="r1", workflow_id="w1")
        out = await handle_util_code(ctx, {"script": "import os\noutput = os.listdir('/')"})
        assert out["success"] is False
        assert "Forbidden" in out["error"]

    @pytest.mark.asyncio
    async def test_util_code_runs_simple_script(self):
        from core.workflow.models import RunContext
        from core.workflow.nodes.util import handle_util_code

        ctx = RunContext(run_id="r1", workflow_id="w1", trigger_payload={"n": 4})
        out = await handle_util_code(ctx, {"script": "output = sum(range(int(trigger['n'])))"})
        assert out["success"] is True
        assert out["output"] == 6


class TestWorkflowValidatorNew:
    def test_http_node_requires_url(self):
        from core.workflow.models import WorkflowDefinition
        from core.workflow.validator import validate_workflow

        defn = WorkflowDefinition.from_dict({
            "nodes": [{"id": "h1", "type": "action.http", "config": {}}],
            "edges": [],
        })
        result = validate_workflow(defn)
        assert result["valid"] is False
        assert any("url" in e.lower() for e in result["errors"])

    def test_code_node_blocks_imports(self):
        from core.workflow.models import WorkflowDefinition
        from core.workflow.validator import validate_workflow

        defn = WorkflowDefinition.from_dict({
            "nodes": [{"id": "c1", "type": "util.code", "config": {"script": "import os"}}],
            "edges": [],
        })
        result = validate_workflow(defn)
        assert result["valid"] is False
