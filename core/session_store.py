"""Shared session store path resolution."""

from __future__ import annotations

import os
from pathlib import Path


def get_state_db_path() -> str:
    """Return SQLite path for chat session storage.

    Prefers STATE_DB_PATH, then DATABASE_URL (sqlite), else unified agent.db.
    """
    explicit = os.environ.get("STATE_DB_PATH")
    if explicit:
        return explicit
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "", 1)
    return "data/agent.db"


def ensure_state_db_dir(db_path: str) -> None:
    """Create parent directory for the session database file."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
