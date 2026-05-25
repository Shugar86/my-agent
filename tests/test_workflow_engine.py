"""Workflow engine tests."""

from __future__ import annotations

import json
import os
import pytest
from unittest.mock import AsyncMock, patch

from core.user_manager import UserManager

os.environ["ENV"] = "test"
os.environ.setdefault("DATABASE_URL", "sqlite:///data/test_workflow.db")


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Fresh test database per test."""
    db_path = tmp_path / "test_agent.db"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from core.db_migrate import run_migrations
    from core.db_manager import DBManager
    import core.db_manager as dm
    dm.db = DBManager(f"sqlite:///{db_path}")
    run_migrations(f"sqlite:///{db_path}")
    yield


class TestWorkflowDefinition:
    def test_from_dict_and_topological_sort(self):
        from core.workflow.models import WorkflowDefinition
        from core.workflow.executor import WorkflowExecutor

        definition = WorkflowDefinition.from_dict({
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {"prompt": "hi"}},
                {"id": "x1", "type": "action.webhook", "config": {"url": "http://example.com"}},
            ],
            "edges": [
                {"from": "t1", "to": "a1"},
                {"from": "a1", "to": "x1"},
            ],
        })
        executor = WorkflowExecutor()
        order = executor._topological_sort(definition)
        assert order.index("t1") < order.index("a1") < order.index("x1")

    def test_cycle_detection(self):
        from core.workflow.models import WorkflowDefinition
        from core.workflow.executor import WorkflowExecutor

        definition = WorkflowDefinition.from_dict({
            "nodes": [
                {"id": "a", "type": "trigger.webhook", "config": {}},
                {"id": "b", "type": "agent.skill", "config": {}},
            ],
            "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}],
        })
        executor = WorkflowExecutor()
        with pytest.raises(ValueError, match="cycle"):
            executor._topological_sort(definition)


class TestWorkflowStore:
    def test_crud_workflow(self):
        from core.workflow.store import WorkflowStore

        store = WorkflowStore()
        wf = store.create_workflow("Test WF", {"nodes": [], "edges": []}, owner_id="u1")
        assert wf["name"] == "Test WF"
        assert wf["id"].startswith("wf_")

        listed = store.list_workflows(owner_id="u1")
        assert len(listed) == 1

        updated = store.update_workflow(wf["id"], name="Updated")
        assert updated["name"] == "Updated"

        assert store.delete_workflow(wf["id"])


class TestWorkflowExecutor:
    @pytest.mark.asyncio
    async def test_happy_path_mock_handlers(self):
        from core.workflow.store import WorkflowStore
        from core.workflow.executor import WorkflowExecutor
        from core.workflow.registry import register_node_handler, reset_registry
        import core.workflow.executor as exec_mod

        reset_registry()
        exec_mod._handlers_registered = False

        store = WorkflowStore()
        wf = store.create_workflow("Exec Test", {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "a1", "type": "agent.skill", "config": {}},
            ],
            "edges": [{"from": "t1", "to": "a1"}],
        }, owner_id="u1")

        async def mock_trigger(ctx, config):
            return {"output": "triggered"}

        async def mock_agent(ctx, config):
            return {"output": "agent result"}

        register_node_handler("trigger.webhook", mock_trigger)
        register_node_handler("agent.skill", mock_agent)
        exec_mod._handlers_registered = True

        executor = WorkflowExecutor(store=store)
        result = await executor.run(wf["id"], trigger_payload={"test": True})
        assert result["success"] is True
        assert result["run_id"].startswith("run_")

    @pytest.mark.asyncio
    async def test_condition_node(self):
        from core.workflow.models import RunContext
        from core.workflow.nodes.condition import handle_condition

        ctx = RunContext(run_id="r1", workflow_id="w1")
        ctx.node_outputs["a1"] = {"output": "contains error message"}
        result = await handle_condition(ctx, {
            "source_node": "a1", "field": "output", "operator": "contains", "value": "error"
        })
        assert result["branch"] == "true"


    @pytest.mark.asyncio
    async def test_condition_false_branch_skipped(self):
        from core.workflow.store import WorkflowStore
        from core.workflow.executor import WorkflowExecutor
        from core.workflow.registry import register_node_handler, reset_registry
        import core.workflow.executor as exec_mod

        reset_registry()
        exec_mod._handlers_registered = False

        executed_nodes: list[str] = []

        async def mock_trigger(ctx, config):
            executed_nodes.append("t1")
            return {"output": "ok"}

        async def mock_condition(ctx, config):
            executed_nodes.append("c1")
            return {"branch": "false"}

        async def mock_true_action(ctx, config):
            executed_nodes.append("x_true")
            return {"output": "true branch"}

        async def mock_false_action(ctx, config):
            executed_nodes.append("x_false")
            return {"output": "false branch"}

        register_node_handler("trigger.webhook", mock_trigger)
        register_node_handler("condition", mock_condition)
        register_node_handler("action.webhook", mock_true_action)
        register_node_handler("action.telegram", mock_false_action)
        exec_mod._handlers_registered = True

        store = WorkflowStore()
        wf = store.create_workflow("Branch Test", {
            "nodes": [
                {"id": "t1", "type": "trigger.webhook", "config": {}},
                {"id": "c1", "type": "condition", "config": {}},
                {"id": "x_true", "type": "action.webhook", "config": {}},
                {"id": "x_false", "type": "action.telegram", "config": {}},
            ],
            "edges": [
                {"from": "t1", "to": "c1"},
                {"from": "c1", "to": "x_true", "label": "true"},
                {"from": "c1", "to": "x_false", "label": "false"},
            ],
        })

        executor = WorkflowExecutor(store=store)
        result = await executor.run(wf["id"])
        assert result["success"] is True
        assert "x_true" not in executed_nodes
        assert "x_false" in executed_nodes


class TestWorkflowValidator:
    def test_validate_detects_cycle(self):
        from core.workflow.models import WorkflowDefinition
        from core.workflow.validator import validate_workflow

        definition = WorkflowDefinition.from_dict({
            "nodes": [
                {"id": "a", "type": "trigger.webhook", "config": {}},
                {"id": "b", "type": "agent.skill", "config": {}},
            ],
            "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}],
        })
        result = validate_workflow(definition)
        assert result["valid"] is False
        assert any("cycle" in e.lower() for e in result["errors"])

    def test_validate_invalid_cron(self):
        from core.workflow.models import WorkflowDefinition
        from core.workflow.validator import validate_workflow

        definition = WorkflowDefinition.from_dict({
            "nodes": [{"id": "t1", "type": "trigger.schedule", "config": {"cron": "invalid"}}],
            "edges": [],
        })
        result = validate_workflow(definition)
        assert result["valid"] is False


class TestScheduleSync:
    @pytest.mark.asyncio
    async def test_sync_schedule_on_active_workflow(self):
        from core.workflow.store import WorkflowStore
        from core.workflow.executor import WorkflowExecutor
        from unittest.mock import AsyncMock, patch

        store = WorkflowStore()
        wf = store.create_workflow("Scheduled", {
            "nodes": [{"id": "s1", "type": "trigger.schedule", "config": {"cron": "0 9 * * *"}}],
            "edges": [],
        }, status="active")

        executor = WorkflowExecutor(store=store)
        with patch("core.scheduler_manager.scheduler_manager.add_workflow_job", new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {"success": True}
            jobs = await executor.sync_schedule_triggers(wf["id"])
            assert len(jobs) == 1
            mock_add.assert_called_once()


class TestWorkflowAPI:
    @pytest.fixture
    async def client(self, tmp_path, monkeypatch):
        db_path = tmp_path / "api_test.db"
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from core.db_migrate import run_migrations
        import core.db_manager as dm
        dm.db = __import__("core.db_manager", fromlist=["DBManager"]).DBManager(f"sqlite:///{db_path}")
        run_migrations(f"sqlite:///{db_path}")

        from httpx import ASGITransport, AsyncClient
        from web.server import app, user_manager
        from core.auth import create_access_token

        um = UserManager()
        import web.server as ws
        ws.user_manager = um
        await um.connect()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as c:
            token = create_access_token({"sub": "admin", "user_id": "u_admin", "role": "admin"})
            c.cookies.set("access_token", token)
            # Mark onboarding complete to avoid redirect
            from core.workflow.store import workflow_store
            workflow_store.set_onboarding_complete("u_admin", True)
            yield c
        await um.close()

    @pytest.mark.asyncio
    async def test_create_and_run_workflow(self, client):
        async def mock_trigger(ctx, config):
            return {"output": "ok"}

        from core.workflow.registry import register_node_handler, reset_registry
        import core.workflow.executor as exec_mod
        reset_registry()
        register_node_handler("trigger.webhook", mock_trigger)
        exec_mod._handlers_registered = True

        resp = await client.post("/api/workflows", json={
            "name": "API Test",
            "definition": {
                "nodes": [{"id": "t1", "type": "trigger.webhook", "config": {}}],
                "edges": [],
            },
        })
        assert resp.status_code == 200
        wf_id = resp.json()["id"]

        run_resp = await client.post(f"/api/workflows/{wf_id}/run", json={"payload": {"hello": "world"}})
        assert run_resp.status_code == 200
        assert run_resp.json()["success"] is True

    @pytest.mark.asyncio
    async def test_validate_workflow(self, client):
        resp = await client.post("/api/workflows/validate", json={
            "definition": {
                "nodes": [{"id": "t1", "type": "trigger.schedule", "config": {"cron": "0 9 * * *"}}],
                "edges": [],
            },
        })
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_list_runs(self, client):
        resp = await client.post("/api/workflows", json={
            "name": "Runs Test",
            "definition": {"nodes": [], "edges": []},
        })
        wf_id = resp.json()["id"]
        runs_resp = await client.get(f"/api/workflows/{wf_id}/runs")
        assert runs_resp.status_code == 200
        assert "runs" in runs_resp.json()

    @pytest.mark.asyncio
    async def test_list_templates(self, client):
        from core.db_migrate import run_migrations
        import core.db_manager as dm
        run_migrations()
        # Insert one template directly
        dm.db.execute(
            """INSERT OR IGNORE INTO workflow_templates
               (id, name, description, category, definition_json, tags_json, installs_count)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("tpl_test", "Test", "Test template", "ops", "{}", "[]", 0),
        )
        resp = await client.get("/api/workflow-templates")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
