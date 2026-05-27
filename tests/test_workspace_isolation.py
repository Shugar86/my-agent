"""Workspace isolation tests — cross-tenant access must be denied."""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from core.user_manager import UserManager
from web.server import app


@pytest.fixture
async def client(monkeypatch, tmp_path):
    """Isolated test DB with connected user manager."""
    os.makedirs("data", exist_ok=True)
    os.environ["ENV"] = "test"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db_path = tmp_path / "isolation_test.db"
    import core.db_manager as dm
    from core.db_migrate import run_migrations

    dm.db = dm.DBManager(f"sqlite:///{db_path}")
    run_migrations(f"sqlite:///{db_path}")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    import web.server as ws

    ws.db = dm.db
    ws.user_manager = UserManager()
    await ws.user_manager.connect()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac
    await ws.user_manager.close()


@pytest.mark.asyncio
async def test_run_list_requires_workflow_access(client):
    """User cannot list runs for a workflow they do not own."""
    suffix = "iso_a"
    reg_a = await client.post(
        "/api/register",
        json={"username": f"iso_user_{suffix}", "password": "SecurePass123!"},
    )
    assert reg_a.status_code == 200

    create = await client.post(
        "/api/workflows",
        json={
            "name": "Private WF",
            "definition": {"nodes": [], "edges": []},
        },
    )
    assert create.status_code == 200
    wf_id = create.json()["id"]

    await client.post("/api/logout")

    reg_b = await client.post(
        "/api/register",
        json={"username": f"iso_user_b_{suffix}", "password": "SecurePass456!"},
    )
    assert reg_b.status_code == 200

    runs_resp = await client.get(f"/api/workflows/{wf_id}/runs")
    assert runs_resp.status_code == 403
