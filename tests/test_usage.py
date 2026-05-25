"""Usage ledger tests."""

from __future__ import annotations

import os
import pytest

os.environ["ENV"] = "test"


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test_usage.db"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from core.db_migrate import run_migrations
    from core.db_manager import DBManager
    import core.db_manager as dm

    dm.db = DBManager(f"sqlite:///{db_path}")
    run_migrations(f"sqlite:///{db_path}")
    yield


def test_track_and_summary():
    from core.usage.tracker import usage_tracker

    usage_tracker.track("chat_stream", team_id="team_x", user_id="u1", tokens=100, cost_usd=0.001)
    usage_tracker.track("workflow_run", team_id="team_x", user_id="u1", metadata={"workflow_id": "wf_1"})
    summary = usage_tracker.summary("team_x", period_days=7)
    assert summary["total_tokens"] >= 100
    assert summary["workflow_runs"] >= 1
    events = usage_tracker.list_events("team_x", limit=10)
    assert len(events) >= 2
