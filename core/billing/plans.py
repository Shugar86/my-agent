"""Workspace plan tiers and usage limits."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from core import db_manager as _dm


@dataclass(frozen=True)
class PlanLimits:
    """Monthly limits for a workspace plan."""

    workflow_runs: int
    label: str


PLAN_LIMITS: dict[str, PlanLimits] = {
    "free": PlanLimits(workflow_runs=50, label="Free"),
    "pro": PlanLimits(workflow_runs=5000, label="Pro"),
    "team": PlanLimits(workflow_runs=50000, label="Team"),
}


def get_plan_limits(plan: str) -> PlanLimits:
    """Return limits for plan id (defaults to free)."""
    return PLAN_LIMITS.get(plan or "free", PLAN_LIMITS["free"])


def count_workflow_runs_this_month(team_id: str) -> int:
    """Count workflow_run usage events for current calendar month."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    row = _dm.db.fetchone(
        """SELECT COUNT(*) AS cnt FROM usage_events
           WHERE team_id = ? AND action = 'workflow_run' AND created_at >= ?""",
        (team_id, month_start),
    )
    return int(row["cnt"]) if row else 0


def check_workflow_run_allowed(team_id: str | None, plan: str) -> dict[str, Any]:
    """Return whether another workflow run is allowed under plan limits."""
    if not team_id:
        return {"allowed": True, "plan": plan or "free", "used": 0, "limit": None}
    limits = get_plan_limits(plan)
    used = count_workflow_runs_this_month(team_id)
    return {
        "allowed": used < limits.workflow_runs,
        "plan": plan or "free",
        "used": used,
        "limit": limits.workflow_runs,
        "label": limits.label,
    }
