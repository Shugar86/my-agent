"""Smoke tests for the canonical Competitor Intelligence demo flow."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from core.workflow.store import workflow_store
from scripts.generate_demo_artifact import generate_all
from scripts.seed_workflow_templates import seed as seed_templates
from web.server import app


@pytest.fixture
async def demo_client(monkeypatch, tmp_path):
    """HTTP client with seeded competitor template and demo DOCX."""
    os.environ["ENV"] = "test"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("NEUROAPI_API_KEY", raising=False)

    db_path = tmp_path / "demo_flow_test.db"
    import core.db_manager as dm
    from core.db_migrate import run_migrations

    dm.db = dm.DBManager(f"sqlite:///{db_path}")
    run_migrations(f"sqlite:///{db_path}")
    dm.db.create_tables()

    import web.server as ws

    ws.db = dm.db
    ws.user_manager = __import__("core.user_manager", fromlist=["UserManager"]).UserManager()
    await ws.user_manager.connect()

    seed_templates()
    generate_all(force=False)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        yield client

    await ws.user_manager.close()


async def _instant_mock_logs(
    run_id: str,
    sample: dict,
    target: str,
    preset: str,
) -> None:
    """Replay mock logs without delays for fast CI."""
    logs = [
        {
            "node_id": event.get("node_id"),
            "event": event.get("event"),
            "detail": event.get("detail", {}),
        }
        for event in sample.get("events", [])
    ]
    workflow_store.update_run_logs(run_id, logs, status="running")
    workflow_store.finish_run(run_id, "success", logs)


class TestCanonicalDemoFlow:
    """Public competitor demo: run → poll → DOCX artifact."""

    @pytest.mark.asyncio
    async def test_public_run_returns_mock_payload(self, demo_client):
        with patch("web.demo_router._stream_mock_logs", _instant_mock_logs):
            response = await demo_client.post(
                "/api/demo/public/run",
                json={
                    "preset": "competitor",
                    "target": "Notion",
                    "our_company": "Linear",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "mock"
        assert data["preset"] == "competitor"
        assert data["run_id"]
        assert len(data["node_order"]) == 7
        assert data["artifact_url"] == "/api/demo/artifact/competitor_brief_notion_vs_linear.docx"

    @pytest.mark.asyncio
    async def test_public_run_polls_to_success(self, demo_client):
        with patch("web.demo_router._stream_mock_logs", _instant_mock_logs):
            start = await demo_client.post(
                "/api/demo/public/run",
                json={"preset": "competitor", "target": "Notion", "our_company": "Linear"},
            )
        assert start.status_code == 200
        run_id = start.json()["run_id"]

        status = "running"
        for _ in range(50):
            poll = await demo_client.get(f"/api/demo/public/runs/{run_id}?preset=competitor")
            assert poll.status_code == 200
            status = poll.json()["status"]
            if status in ("success", "failed"):
                break
            await asyncio.sleep(0.05)

        assert status == "success"
        body = poll.json()
        assert len(body["node_order"]) == 7
        assert body["artifact_url"] == "/api/demo/artifact/competitor_brief_notion_vs_linear.docx"

    @pytest.mark.asyncio
    async def test_artifact_download_docx(self, demo_client):
        response = await demo_client.get("/api/demo/artifact/competitor_brief_notion_vs_linear.docx")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert len(response.content) > 1000

    @pytest.mark.asyncio
    async def test_demo_sample_competitor_preset(self, demo_client):
        response = await demo_client.get("/api/demo/sample?preset=competitor")
        assert response.status_code == 200
        data = response.json()
        assert data["preset"] == "competitor"
        assert len(data["node_order"]) == 7
        assert data["default_payload"]["target"] == "Notion"
