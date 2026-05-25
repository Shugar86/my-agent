"""Notion API integration skill."""

from __future__ import annotations

import logging
import os
from typing import Any

from core.integration_credentials import get_credentials

logger = logging.getLogger(__name__)


def _get_notion_client(user_id: str | None = None):
    """Build Notion client."""
    try:
        from notion_client import Client
    except ImportError as exc:
        raise RuntimeError("notion-client not installed") from exc

    creds = get_credentials(user_id, "notion")
    api_key = creds.get("api_key") or os.environ.get("NOTION_API_KEY", "")
    if not api_key:
        raise ValueError("NOTION_API_KEY not configured")
    return Client(auth=api_key)


def notion_create_page(
    parent_id: str,
    title: str,
    content: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Create a Notion page."""
    try:
        client = _get_notion_client(user_id)
        result = client.pages.create(
            parent={"page_id": parent_id},
            properties={"title": {"title": [{"text": {"content": title}}]}},
            children=[
                {"object": "block", "type": "paragraph",
                 "paragraph": {"rich_text": [{"text": {"content": content[:2000]}}]}}
            ],
        )
        return {"success": True, "page_id": result.get("id"), "url": result.get("url")}
    except Exception as exc:
        logger.exception("Notion create page failed")
        return {"success": False, "error": str(exc)}


def notion_update_database(
    database_id: str,
    properties: dict,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Create a new entry in a Notion database."""
    try:
        client = _get_notion_client(user_id)
        result = client.pages.create(parent={"database_id": database_id}, properties=properties)
        return {"success": True, "page_id": result.get("id")}
    except Exception as exc:
        logger.exception("Notion database update failed")
        return {"success": False, "error": str(exc)}


def register_tools() -> None:
    """Register Notion tools."""
    from core.tool_registry import registry

    registry.register(
        name="notion_create_page",
        description="Create a Notion page",
        parameters={"type": "object", "properties": {
            "parent_id": {"type": "string"}, "title": {"type": "string"}, "content": {"type": "string"},
        }},
        execute_fn=lambda parent_id="", title="", content="", user_id=None:
            notion_create_page(parent_id, title, content, user_id),
    )
