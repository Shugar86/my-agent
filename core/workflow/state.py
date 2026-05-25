"""Persistent workflow state between runs."""

from __future__ import annotations

import json
from typing import Any

from core import db_manager as _dm


def _db():
    return _dm.db


def load_state(workflow_id: str) -> dict[str, Any]:
    """Load all key-value state for a workflow."""
    rows = _db().fetchall(
        "SELECT key, value_json FROM workflow_state WHERE workflow_id = ?",
        (workflow_id,),
    )
    state: dict[str, Any] = {}
    for row in rows:
        try:
            state[row["key"]] = json.loads(row["value_json"] or "null")
        except json.JSONDecodeError:
            state[row["key"]] = row["value_json"]
    return state


def save_state(workflow_id: str, state: dict[str, Any]) -> None:
    """Persist workflow state keys."""
    for key, value in state.items():
        existing = _db().fetchone(
            "SELECT id FROM workflow_state WHERE workflow_id = ? AND key = ?",
            (workflow_id, key),
        )
        val_json = json.dumps(value)
        if existing:
            _db().execute(
                "UPDATE workflow_state SET value_json = ?, updated_at = datetime('now') WHERE workflow_id = ? AND key = ?",
                (val_json, workflow_id, key),
            )
        else:
            _db().execute(
                "INSERT INTO workflow_state (workflow_id, key, value_json) VALUES (?, ?, ?)",
                (workflow_id, key, val_json),
            )
