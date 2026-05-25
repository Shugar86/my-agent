"""Phase 3 B2B: teams, usage, Google auth tests."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

os.environ["ENV"] = "test"
os.environ.setdefault("DATABASE_URL", "sqlite:///data/test_phase3.db")


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Fresh database per test."""
    db_path = tmp_path / "test_phase3.db"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from core.db_migrate import run_migrations
    from core.db_manager import DBManager
    import core.db_manager as dm

    dm.db = DBManager(f"sqlite:///{db_path}")
    run_migrations(f"sqlite:///{db_path}")
    yield


class TestTeamStore:
    def test_create_and_list_teams(self):
        from core.teams.store import team_store

        team = team_store.create_team("Acme Corp", "u_test1")
        assert team["name"] == "Acme Corp"
        teams = team_store.list_teams_for_user("u_test1")
        assert len(teams) == 1
        assert teams[0]["member_role"] == "owner"

    def test_invite_and_accept(self):
        from core.teams.store import team_store

        team = team_store.create_team("Beta Team", "u_owner")
        invite = team_store.create_invite(team["id"], "member@example.com", role="member")
        accepted = team_store.accept_invite(invite["token"], "u_member")
        assert accepted is not None
        assert team_store.get_member_role(team["id"], "u_member") == "member"

    def test_ensure_personal_team(self):
        from core.teams.store import team_store

        team = team_store.ensure_personal_team("u_new", "alice")
        assert team["id"]
        teams = team_store.list_teams_for_user("u_new")
        assert len(teams) >= 1

    def test_workflow_workspace_scoping(self):
        from core.teams.store import team_store
        from core.workflow.store import WorkflowStore

        team = team_store.create_team("WF Team", "u_wf")
        store = WorkflowStore()
        wf = store.create_workflow("Test", {"nodes": [], "edges": []}, owner_id="u_wf", workspace_id=team["id"])
        listed = store.list_workflows(workspace_id=team["id"])
        assert len(listed) == 1
        assert listed[0]["id"] == wf["id"]
        assert store.user_can_access_workflow(wf["id"], "u_wf", min_role="member")


class TestTeamsAPI:
    @pytest.mark.asyncio
    async def test_teams_crud_via_client(self):
        from httpx import ASGITransport, AsyncClient
        from web.server import app
        from core.auth import create_access_token

        token = create_access_token({"sub": "tester", "user_id": "u_api", "role": "user"})
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/teams",
                json={"name": "API Team"},
                cookies={"access_token": token},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["team"]["name"] == "API Team"

            resp2 = await client.get("/api/teams", cookies={"access_token": token})
            assert resp2.status_code == 200
            assert resp2.json()["total"] >= 1
