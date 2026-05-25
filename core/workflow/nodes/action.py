"""Action node handlers — integrations."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from core.workflow.models import RunContext
from core.workflow.registry import register_node_handler

logger = logging.getLogger(__name__)


async def handle_action_telegram(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Send Telegram message."""
    from skills.messaging.skill import send_message

    resolved = ctx.resolve_config(config)
    result = send_message(
        platform="telegram",
        recipient=resolved.get("chat_id", ""),
        message=resolved.get("message", ""),
    )
    return {"output": result, "success": result.get("success", False)}


async def handle_action_slack(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Send Slack message."""
    from skills.messaging.skill import send_message

    resolved = ctx.resolve_config(config)
    result = send_message(
        platform="slack",
        recipient=resolved.get("channel", ""),
        message=resolved.get("message", ""),
    )
    return {"output": result, "success": result.get("success", False)}


async def handle_action_gmail(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Send email via Gmail API."""
    from skills.gmail.skill import gmail_send

    resolved = ctx.resolve_config(config)
    result = gmail_send(
        to=resolved.get("to", ""),
        subject=resolved.get("subject", ""),
        body=resolved.get("body", ""),
        user_id=ctx.user_id,
    )
    return {"output": result, "success": result.get("success", False)}


async def handle_action_sheets_read(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Read Google Sheets range."""
    from skills.google_sheets.skill import sheets_read

    resolved = ctx.resolve_config(config)
    result = sheets_read(
        spreadsheet_id=resolved.get("spreadsheet_id", ""),
        range_name=resolved.get("range", "Sheet1!A1:Z100"),
        user_id=ctx.user_id,
    )
    return {"output": result, "success": result.get("success", False)}


async def handle_action_sheets_write(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Write to Google Sheets."""
    from skills.google_sheets.skill import sheets_write

    resolved = ctx.resolve_config(config)
    result = sheets_write(
        spreadsheet_id=resolved.get("spreadsheet_id", ""),
        range_name=resolved.get("range", "Sheet1!A1"),
        values=resolved.get("values", []),
        user_id=ctx.user_id,
    )
    return {"output": result, "success": result.get("success", False)}


async def handle_action_notion_page(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Create Notion page."""
    from skills.notion.skill import notion_create_page

    resolved = ctx.resolve_config(config)
    result = notion_create_page(
        parent_id=resolved.get("parent_id", ""),
        title=resolved.get("title", "Workflow Page"),
        content=resolved.get("content", ""),
        user_id=ctx.user_id,
    )
    return {"output": result, "success": result.get("success", False)}


async def handle_action_notion_db(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Update Notion database entry."""
    from skills.notion.skill import notion_update_database

    resolved = ctx.resolve_config(config)
    result = notion_update_database(
        database_id=resolved.get("database_id", ""),
        properties=resolved.get("properties", {}),
        user_id=ctx.user_id,
    )
    return {"output": result, "success": result.get("success", False)}


async def handle_action_webhook(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """POST to external webhook URL."""
    resolved = ctx.resolve_config(config)
    url = resolved.get("url", "")
    payload = resolved.get("payload", {})
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            return {
                "output": {"status_code": resp.status_code, "body": resp.text[:2000]},
                "success": resp.is_success,
            }
    except httpx.HTTPError as exc:
        logger.warning("Webhook action failed: %s", exc)
        return {"output": {"error": str(exc)}, "success": False}


def register_action_handlers() -> None:
    """Register all action node handlers."""
    register_node_handler("action.telegram", handle_action_telegram)
    register_node_handler("action.slack", handle_action_slack)
    register_node_handler("action.gmail_send", handle_action_gmail)
    register_node_handler("action.sheets_read", handle_action_sheets_read)
    register_node_handler("action.sheets_write", handle_action_sheets_write)
    register_node_handler("action.notion_page", handle_action_notion_page)
    register_node_handler("action.notion_db_update", handle_action_notion_db)
    register_node_handler("action.webhook", handle_action_webhook)
