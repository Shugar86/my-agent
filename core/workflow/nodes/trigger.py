"""Trigger node handlers."""

from __future__ import annotations

import logging
from typing import Any

from core.workflow.models import RunContext
from core.workflow.registry import register_node_handler

logger = logging.getLogger(__name__)


async def handle_trigger_webhook(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Pass through webhook trigger payload."""
    output = {"output": ctx.trigger_payload, **ctx.trigger_payload}
    ctx.node_outputs["trigger"] = output
    return output


async def handle_trigger_schedule(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Schedule trigger — payload from scheduler."""
    output = {"output": "scheduled", "scheduled_at": config.get("scheduled_at", ""), **ctx.trigger_payload}
    ctx.node_outputs["trigger"] = output
    return output


async def handle_trigger_email(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Email trigger — pass through polled messages or stub for manual runs."""
    emails = ctx.trigger_payload.get("emails", [])
    if emails:
        output = {"output": f"{len(emails)} new email(s)", "emails": emails, **ctx.trigger_payload}
    else:
        output = {"output": "email_trigger", **ctx.trigger_payload}
    ctx.node_outputs["trigger"] = output
    return output


async def handle_trigger_telegram(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Telegram message trigger."""
    output = {"output": ctx.trigger_payload.get("text", ""), **ctx.trigger_payload}
    ctx.node_outputs["trigger"] = output
    return output


async def handle_trigger_new_lead(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """New lead trigger stub."""
    output = {"output": "new_lead", **ctx.trigger_payload}
    ctx.node_outputs["trigger"] = output
    return output


def register_trigger_handlers() -> None:
    """Register all trigger node handlers."""
    register_node_handler("trigger.webhook", handle_trigger_webhook)
    register_node_handler("trigger.schedule", handle_trigger_schedule)
    register_node_handler("trigger.email", handle_trigger_email)
    register_node_handler("trigger.telegram", handle_trigger_telegram)
    register_node_handler("trigger.new_lead", handle_trigger_new_lead)
