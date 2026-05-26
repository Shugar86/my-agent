"""Production hardening tests for v3.4."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch


def test_validate_production_rejects_sqlite(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    from core.db_manager import DBManager

    mgr = DBManager.__new__(DBManager)
    mgr.database_url = "sqlite:///data/agent.db"
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        mgr._validate_production_config()


def test_validate_production_allows_postgres_url(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    from core.db_manager import DBManager

    mgr = DBManager.__new__(DBManager)
    mgr.database_url = "postgresql://agent:pass@db:5432/agent_db"
    mgr._validate_production_config()  # no raise


@pytest.mark.asyncio
async def test_run_queue_enqueue_calls_redis():
    from core.workflow import run_queue

    with patch("core.workflow.run_queue.redis_client") as mock_redis:
        mock_redis.queue_push = AsyncMock(return_value=True)
        ok = await run_queue.enqueue_run("run_1", "wf_1", {"x": 1}, "u_1")
        assert ok is True
        mock_redis.queue_push.assert_called_once()


@pytest.mark.asyncio
async def test_recover_stale_jobs_moves_processing_to_pending():
    from core.workflow import run_queue

    with patch("core.workflow.run_queue.redis_client") as mock_redis:
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.queue_range = AsyncMock(return_value=['{"run_id":"r1"}'])
        mock_redis.queue_push = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=True)
        count = await run_queue.recover_stale_jobs()
        assert count == 1
        mock_redis.queue_push.assert_called_once()
