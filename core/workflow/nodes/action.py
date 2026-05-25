"""Action node handlers — integrations."""

from __future__ import annotations

import logging
import os
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
    """HTTP request to external webhook URL (GET or POST by default)."""
    resolved = ctx.resolve_config(config)
    url = str(resolved.get("url", "")).strip()
    if not url:
        return {"output": {"error": "url is required"}, "success": False}

    method = str(resolved.get("method", "POST")).upper()
    payload = resolved.get("payload", {})
    headers = resolved.get("headers") or {}
    try:
        timeout = float(resolved.get("timeout", 30))
    except (TypeError, ValueError):
        timeout = 30.0
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method == "GET":
                resp = await client.get(url, headers=headers, params=payload or None)
            elif method == "POST":
                resp = await client.post(url, json=payload, headers=headers)
            else:
                resp = await client.request(method, url, json=payload, headers=headers)
            return {
                "output": {"status_code": resp.status_code, "body": resp.text[:2000]},
                "success": resp.is_success,
            }
    except httpx.HTTPError as exc:
        logger.warning("Webhook action failed: %s", exc)
        return {"output": {"error": str(exc)}, "success": False}


async def handle_action_http(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Generic HTTP request node (GET/POST/PUT/DELETE/PATCH).

    Config keys: ``url``, ``method`` (default GET), ``headers``, ``query``,
    ``json`` (body), ``body`` (raw text), ``timeout`` (seconds, default 30).
    """
    resolved = ctx.resolve_config(config)
    url = str(resolved.get("url", "")).strip()
    if not url:
        return {"output": {"error": "url is required"}, "success": False}

    method = str(resolved.get("method", "GET")).upper()
    headers = resolved.get("headers") or {}
    query = resolved.get("query") or resolved.get("params") or None
    json_body = resolved.get("json")
    raw_body = resolved.get("body")
    try:
        timeout = float(resolved.get("timeout", 30))
    except (TypeError, ValueError):
        timeout = 30.0
    timeout = max(1.0, min(timeout, 120.0))

    if not isinstance(headers, dict):
        headers = {}

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            kwargs: dict[str, Any] = {"headers": headers}
            if query:
                kwargs["params"] = query
            if json_body is not None:
                kwargs["json"] = json_body
            elif raw_body is not None:
                kwargs["content"] = raw_body
            resp = await client.request(method, url, **kwargs)
            try:
                parsed: Any = resp.json()
            except ValueError:
                parsed = resp.text[:4000]
            return {
                "output": {
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers),
                    "body": parsed,
                },
                "success": resp.is_success,
            }
    except httpx.HTTPError as exc:
        logger.warning("HTTP action failed: %s", exc)
        return {"output": {"error": str(exc)}, "success": False}


async def handle_action_n8n(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Trigger n8n workflow via webhook with optional Basic Auth.

    Resolves URL from node config first, then falls back to ``N8N_WEBHOOK_URL`` env var.
    Picks up ``N8N_BASIC_AUTH_USER`` / ``N8N_BASIC_AUTH_PASS`` automatically if set.

    Trade-off: keeping a thin wrapper over httpx (instead of an n8n SDK) means we
    avoid an extra dependency while supporting any self-hosted n8n instance.
    """
    resolved = ctx.resolve_config(config)
    url = str(resolved.get("url") or os.getenv("N8N_WEBHOOK_URL", "")).strip()
    if not url:
        return {"output": {"error": "n8n url not configured"}, "success": False}

    headers = resolved.get("headers") or {}
    if not isinstance(headers, dict):
        headers = {}
    payload = resolved.get("payload", {})

    auth_user = os.getenv("N8N_BASIC_AUTH_USER")
    auth_pass = os.getenv("N8N_BASIC_AUTH_PASS")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            kwargs: dict[str, Any] = {"json": payload, "headers": headers}
            if auth_user and auth_pass:
                kwargs["auth"] = (auth_user, auth_pass)
            resp = await client.post(url, **kwargs)
            try:
                body: Any = resp.json()
            except ValueError:
                body = resp.text[:1500]
            return {
                "output": {"status_code": resp.status_code, "body": body},
                "success": resp.is_success,
            }
    except httpx.HTTPError as exc:
        logger.warning("n8n webhook failed: %s", exc)
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
    register_node_handler("action.http", handle_action_http)
    register_node_handler("action.n8n_webhook", handle_action_n8n)
