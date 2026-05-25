"""Tests for Phase 2 DoD closure features."""

from __future__ import annotations

import json
import os
import pytest

os.environ["ENV"] = "test"
os.environ.setdefault("DATABASE_URL", "sqlite:///data/test_dod.db")


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Fresh databases per test."""
    db_path = tmp_path / "test_agent.db"
    state_path = tmp_path / "state.db"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("STATE_DB_PATH", str(state_path))
    from core.db_migrate import run_migrations
    from core.db_manager import DBManager
    import core.db_manager as dm
    dm.db = DBManager(f"sqlite:///{db_path}")
    run_migrations(f"sqlite:///{db_path}")
    dm.db.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_jobs_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            description TEXT,
            result TEXT,
            status TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    yield


class TestRunLogsIncremental:
    def test_update_run_logs_mid_execution(self):
        from core.workflow.store import WorkflowStore

        store = WorkflowStore()
        wf = store.create_workflow("Log Test", {"nodes": [], "edges": []})
        run = store.create_run(wf["id"])
        store.update_run_logs(run["id"], [{"node_id": "a", "event": "started"}])
        fetched = store.get_run(run["id"])
        assert fetched is not None
        assert fetched["status"] == "running"
        assert len(fetched["logs"]) == 1


class TestEmailTriggers:
    @pytest.mark.asyncio
    async def test_register_email_poll_job(self):
        from core.workflow.store import WorkflowStore
        from core.workflow.executor import WorkflowExecutor
        from unittest.mock import AsyncMock, patch

        store = WorkflowStore()
        wf = store.create_workflow("Email WF", {
            "nodes": [{"id": "e1", "type": "trigger.email", "config": {"poll_interval_minutes": 5}}],
            "edges": [],
        }, status="active")

        executor = WorkflowExecutor(store=store)
        with patch("core.scheduler_manager.scheduler_manager.add_email_poll_job", new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {"success": True}
            jobs = await executor.register_email_triggers(wf["id"])
            assert len(jobs) == 1
            mock_add.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_poll_triggers_run_on_new_messages(self):
        from unittest.mock import AsyncMock, patch
        from core.workflow.executor import WorkflowExecutor
        from core.workflow.store import WorkflowStore

        store = WorkflowStore()
        wf = store.create_workflow("Email Run", {
            "nodes": [{"id": "e1", "type": "trigger.email", "config": {}}],
            "edges": [],
        }, owner_id="u1", status="active")

        with patch("skills.gmail.skill.gmail_list_unread") as mock_gmail:
            mock_gmail.return_value = {"success": True, "messages": [{"id": "msg1"}, {"id": "msg2"}]}
            with patch.object(WorkflowExecutor, "run", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = {"success": True, "run_id": "run_test"}
                from core.scheduler_manager import _execute_email_poll
                await _execute_email_poll(wf["id"], "e1", "job1")
                mock_run.assert_called_once()
                call_payload = mock_run.call_args[1]["trigger_payload"]
                assert call_payload.get("email_trigger") is True


class TestSessionsAPI:
    @pytest.fixture
    async def client(self, tmp_path, monkeypatch):
        db_path = tmp_path / "api_test.db"
        state_path = tmp_path / "state.db"
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("STATE_DB_PATH", str(state_path))
        from core.db_migrate import run_migrations
        import core.db_manager as dm
        dm.db = __import__("core.db_manager", fromlist=["DBManager"]).DBManager(f"sqlite:///{db_path}")
        run_migrations(f"sqlite:///{db_path}")

        from httpx import ASGITransport, AsyncClient
        from web.server import app
        from core.auth import create_access_token
        import web.sessions_router as sr
        sr.state_db = __import__("core.state_db", fromlist=["StateDB"]).StateDB(str(state_path))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as c:
            token = create_access_token({"sub": "admin", "user_id": "u_admin", "role": "admin"})
            c.cookies.set("access_token", token)
            from core.workflow.store import workflow_store
            workflow_store.set_onboarding_complete("u_admin", True)
            yield c

    @pytest.mark.asyncio
    async def test_create_and_list_sessions(self, client):
        resp = await client.post("/api/sessions", json={"title": "Test chat", "agent_id": "universal"})
        assert resp.status_code == 200
        session_id = resp.json()["id"]

        list_resp = await client.get("/api/sessions")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1
        assert any(s["id"] == session_id for s in list_resp.json()["sessions"])


class TestWorkflowRunAPI:
    @pytest.fixture
    async def client(self, tmp_path, monkeypatch):
        db_path = tmp_path / "api_test.db"
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from core.db_migrate import run_migrations
        import core.db_manager as dm
        dm.db = __import__("core.db_manager", fromlist=["DBManager"]).DBManager(f"sqlite:///{db_path}")
        run_migrations(f"sqlite:///{db_path}")

        from httpx import ASGITransport, AsyncClient
        from web.server import app
        from core.auth import create_access_token

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as c:
            token = create_access_token({"sub": "admin", "user_id": "u_admin", "role": "admin"})
            c.cookies.set("access_token", token)
            from core.workflow.store import workflow_store
            workflow_store.set_onboarding_complete("u_admin", True)
            yield c

    @pytest.mark.asyncio
    async def test_get_single_run(self, client):
        from core.workflow.store import WorkflowStore

        store = WorkflowStore()
        wf = store.create_workflow("Run API", {"nodes": [], "edges": []})
        run = store.create_run(wf["id"])
        store.update_run_logs(run["id"], [{"node_id": "t1", "event": "started"}])

        resp = await client.get(f"/api/workflows/{wf['id']}/runs/{run['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == run["id"]
        assert data["status"] == "running"


class TestPublishAdminGuard:
    @pytest.fixture
    async def client(self, tmp_path, monkeypatch):
        db_path = tmp_path / "api_test.db"
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from core.db_migrate import run_migrations
        import core.db_manager as dm
        dm.db = __import__("core.db_manager", fromlist=["DBManager"]).DBManager(f"sqlite:///{db_path}")
        run_migrations(f"sqlite:///{db_path}")

        from httpx import ASGITransport, AsyncClient
        from web.server import app
        from core.auth import create_access_token

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as c:
            token = create_access_token({"sub": "user", "user_id": "u_user", "role": "user"})
            c.cookies.set("access_token", token)
            from core.workflow.store import workflow_store
            workflow_store.set_onboarding_complete("u_user", True)
            yield c

    @pytest.mark.asyncio
    async def test_publish_requires_admin(self, client):
        resp = await client.post("/api/workflow-templates", json={
            "name": "User Template",
            "description": "test",
            "category": "ops",
            "definition": {"nodes": [], "edges": []},
        })
        assert resp.status_code == 403
