"""Persistent usage event ledger."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from core import db_manager as _dm


def _db():
    return _dm.db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class UsageTracker:
    """Record and query LLM/workflow usage events."""

    def track(
        self,
        action: str,
        *,
        team_id: str | None = None,
        user_id: str | None = None,
        tokens: int = 0,
        cost_usd: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist a usage event."""
        event_id = f"ue_{uuid.uuid4().hex[:12]}"
        _db().execute(
            """INSERT INTO usage_events
               (id, team_id, user_id, action, tokens, cost_usd, metadata_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event_id,
                team_id,
                user_id,
                action,
                tokens,
                cost_usd,
                json.dumps(metadata or {}),
                _now_iso(),
            ),
        )
        return {"id": event_id, "action": action, "tokens": tokens, "cost_usd": cost_usd}

    def summary(
        self,
        team_id: str,
        period_days: int = 7,
    ) -> dict[str, Any]:
        """Aggregate usage for a team over a period."""
        since = (datetime.now(timezone.utc) - timedelta(days=period_days)).isoformat()
        row = _db().fetchone(
            """SELECT
                 COALESCE(SUM(tokens), 0) AS total_tokens,
                 COALESCE(SUM(cost_usd), 0) AS total_cost,
                 COUNT(*) AS event_count
               FROM usage_events
               WHERE team_id = ? AND created_at >= ?""",
            (team_id, since),
        )
        runs_row = _db().fetchone(
            """SELECT COUNT(*) AS cnt FROM usage_events
               WHERE team_id = ? AND action = 'workflow_run' AND created_at >= ?""",
            (team_id, since),
        )
        daily_rows = _db().fetchall(
            """SELECT date(created_at) AS day,
                      COALESCE(SUM(tokens), 0) AS tokens,
                      COUNT(*) AS events
               FROM usage_events
               WHERE team_id = ? AND created_at >= ?
               GROUP BY date(created_at)
               ORDER BY day ASC""",
            (team_id, since),
        )
        top_wf = _db().fetchall(
            """SELECT json_extract(metadata_json, '$.workflow_id') AS workflow_id,
                      COUNT(*) AS runs
               FROM usage_events
               WHERE team_id = ? AND action = 'workflow_run' AND created_at >= ?
               GROUP BY workflow_id
               ORDER BY runs DESC
               LIMIT 5""",
            (team_id, since),
        )
        return {
            "team_id": team_id,
            "period_days": period_days,
            "total_tokens": int(row["total_tokens"] or 0) if row else 0,
            "total_cost_usd": float(row["total_cost"] or 0) if row else 0.0,
            "event_count": int(row["event_count"] or 0) if row else 0,
            "workflow_runs": int(runs_row["cnt"] or 0) if runs_row else 0,
            "daily": [
                {"day": r["day"], "tokens": int(r["tokens"]), "events": int(r["events"])}
                for r in daily_rows
            ],
            "top_workflows": [
                {"workflow_id": r["workflow_id"], "runs": int(r["runs"])}
                for r in top_wf
                if r["workflow_id"]
            ],
        }

    def list_events(
        self,
        team_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List recent usage events for a team."""
        rows = _db().fetchall(
            """SELECT * FROM usage_events
               WHERE team_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (team_id, limit),
        )
        return [
            {
                "id": r["id"],
                "team_id": r["team_id"],
                "user_id": r["user_id"],
                "action": r["action"],
                "tokens": r["tokens"],
                "cost_usd": r["cost_usd"],
                "metadata": json.loads(r["metadata_json"] or "{}"),
                "created_at": r["created_at"],
            }
            for r in rows
        ]


usage_tracker = UsageTracker()
