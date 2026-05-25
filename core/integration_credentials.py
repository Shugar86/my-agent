"""Integration credentials storage (encrypted at rest)."""

from __future__ import annotations

import json
import logging
from typing import Any

from core.api_keys import encrypt_value, decrypt_value
from core.db_manager import db

logger = logging.getLogger(__name__)


def save_credentials(user_id: str, provider: str, credentials: dict[str, Any]) -> bool:
    """Save or update integration credentials for a user."""
    try:
        encrypted = encrypt_value(json.dumps(credentials))
        existing = db.fetchone(
            "SELECT id FROM integration_credentials WHERE user_id = ? AND provider = ?",
            (user_id, provider),
        )
        if existing:
            db.execute(
                "UPDATE integration_credentials SET credentials_json = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND provider = ?",
                (encrypted, user_id, provider),
            )
        else:
            db.execute(
                "INSERT INTO integration_credentials (user_id, provider, credentials_json) VALUES (?, ?, ?)",
                (user_id, provider, encrypted),
            )
        return True
    except Exception as exc:
        logger.exception("Failed to save credentials for %s/%s: %s", user_id, provider, exc)
        return False


def get_credentials(user_id: str | None, provider: str) -> dict[str, Any]:
    """Load integration credentials for a user, falling back to env vars."""
    import os

    if user_id:
        row = db.fetchone(
            "SELECT credentials_json FROM integration_credentials WHERE user_id = ? AND provider = ?",
            (user_id, provider),
        )
        if row:
            try:
                raw = decrypt_value(row["credentials_json"])
                return json.loads(raw)
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("Failed to decrypt credentials: %s", exc)

    # Fallback to environment variables
    env_map = {
        "google": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", ""),
            "refresh_token": os.environ.get("GOOGLE_REFRESH_TOKEN", ""),
        },
        "notion": {"api_key": os.environ.get("NOTION_API_KEY", "")},
        "telegram": {"bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", "")},
        "slack": {"bot_token": os.environ.get("SLACK_BOT_TOKEN", "")},
    }
    return env_map.get(provider, {})


def delete_credentials(user_id: str, provider: str) -> bool:
    """Delete integration credentials."""
    return db.execute(
        "DELETE FROM integration_credentials WHERE user_id = ? AND provider = ?",
        (user_id, provider),
    ) > 0
