"""A2A (Agent-to-Agent) Protocol endpoints backed by Redis queue."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.config import resolve_agent_model_config
from core.redis_client import redis_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/a2a", tags=["a2a"])

# Fallback when Redis is unavailable (dev/test)
_memory_queue: list[dict[str, Any]] = []
_MEMORY_QUEUE_MAX = 1000

A2A_QUEUE_PREFIX = "a2a:queue:"
A2A_DELIVERED_PREFIX = "a2a:delivered:"


class A2AMessage(BaseModel):
    sender: str
    recipient: str
    type: str = "request"
    content: str
    task_id: str | None = None
    skills: list[str] | None = None
    tools: list[str] | None = None
    ttl: int = 3600


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_at_iso(ttl_seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()


def _is_expired(msg: dict[str, Any]) -> bool:
    expires_at = msg.get("expires_at")
    if not expires_at:
        return False
    return expires_at < _now_iso()


def _queue_key(recipient: str) -> str:
    return f"{A2A_QUEUE_PREFIX}{recipient}"


def _list_agent_ids() -> list[str]:
    from core.agent_store import AgentStore

    return [a["id"] for a in AgentStore().list_agents()]


async def _fanout_broadcast(message: dict[str, Any]) -> None:
    """Deliver broadcast copies to each agent inbox (no shared broadcast queue)."""
    global _memory_queue
    agent_ids = _list_agent_ids()
    if not agent_ids:
        agent_ids = ["*"]

    for agent_id in agent_ids:
        copy = {**message, "recipient": agent_id, "type": "broadcast"}
        payload = json.dumps(copy, ensure_ascii=False)
        pushed = await redis_client.queue_push(_queue_key(agent_id), payload)
        if not pushed:
            _memory_queue.append(copy)
            if len(_memory_queue) > _MEMORY_QUEUE_MAX:
                _memory_queue[:] = _memory_queue[-_MEMORY_QUEUE_MAX:]


async def _enqueue(message: dict[str, Any]) -> None:
    global _memory_queue
    if message.get("type") == "broadcast" or message.get("recipient") == "*":
        await _fanout_broadcast(message)
        return

    recipient = message.get("recipient", "")
    payload = json.dumps(message, ensure_ascii=False)
    pushed = await redis_client.queue_push(_queue_key(recipient), payload)
    if not pushed:
        _memory_queue.append(message)
        if len(_memory_queue) > _MEMORY_QUEUE_MAX:
            _memory_queue[:] = _memory_queue[-_MEMORY_QUEUE_MAX:]


def _message_matches_recipient(msg: dict[str, Any], recipient: str) -> bool:
    return msg.get("recipient") in (recipient, "*") or msg.get("type") == "broadcast"


async def _mark_delivered(message_id: str) -> None:
    """Optional delivery audit trail in Redis (24h TTL)."""
    key = f"{A2A_DELIVERED_PREFIX}{message_id}"
    await redis_client.set(key, _now_iso(), expire=86400)


async def _pop_from_redis_key(key: str, recipient: str, max_items: int = 200) -> list[dict[str, Any]]:
    """Destructively pop messages from a Redis per-agent queue."""
    messages: list[dict[str, Any]] = []

    for _ in range(max_items):
        raw = await redis_client.queue_pop(key)
        if raw is None:
            break
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not _message_matches_recipient(msg, recipient):
            continue
        if _is_expired(msg):
            continue
        messages.append(msg)
    return messages


async def _dequeue_for_recipient(recipient: str) -> list[dict[str, Any]]:
    global _memory_queue
    messages: list[dict[str, Any]] = []

    if await redis_client.ping():
        messages.extend(await _pop_from_redis_key(_queue_key(recipient), recipient))
        return messages

    kept: list[dict[str, Any]] = []
    for msg in _memory_queue:
        if _is_expired(msg):
            continue
        if _message_matches_recipient(msg, recipient):
            messages.append(msg)
        else:
            kept.append(msg)
    _memory_queue = kept
    return messages


def _build_message(msg: A2AMessage, *, message_id: str, msg_type: str | None = None) -> dict[str, Any]:
    ttl = max(1, msg.ttl)
    return {
        "id": message_id,
        "sender": msg.sender,
        "recipient": msg.recipient,
        "type": msg_type or msg.type,
        "content": msg.content,
        "task_id": msg.task_id or message_id,
        "skills": msg.skills or [],
        "tools": msg.tools or [],
        "ttl": ttl,
        "expires_at": _expires_at_iso(ttl),
        "timestamp": _now_iso(),
        "status": "pending",
    }


@router.post("/send")
async def a2a_send(request: Request, msg: A2AMessage) -> dict[str, str]:
    """Send a message to another agent."""
    message_id = f"a2a-{uuid.uuid4().hex[:12]}"
    message = _build_message(msg, message_id=message_id)

    await _enqueue(message)

    if msg.type == "request":
        from core.agent_store import AgentStore

        store = AgentStore()
        recipient_agent = store.get_agent(msg.recipient)
        if recipient_agent:
            try:
                from core.builder import AgentBuilder

                model_config = resolve_agent_model_config(recipient_agent)
                builder = (
                    AgentBuilder()
                    .set_model(model_config)
                    .set_role(recipient_agent.get("role", ""))
                    .set_skills(recipient_agent.get("skills", []))
                    .set_tools(recipient_agent.get("tools", []))
                    .set_memory({"enabled": False})
                )
                agent = builder.build()
                result = await agent.run(msg.content)

                response_msg = {
                    "id": f"a2a-{uuid.uuid4().hex[:12]}",
                    "sender": msg.recipient,
                    "recipient": msg.sender,
                    "type": "response",
                    "content": result,
                    "task_id": message["task_id"],
                    "ttl": message["ttl"],
                    "expires_at": message["expires_at"],
                    "timestamp": _now_iso(),
                    "status": "completed",
                }
                await _enqueue(response_msg)
                message["status"] = "completed"
            except (RuntimeError, ValueError, OSError) as exc:
                message["status"] = "failed"
                message["error"] = str(exc)

    return {
        "message_id": message_id,
        "status": message["status"],
        "timestamp": message["timestamp"],
    }


@router.post("/receive")
async def a2a_receive(request: Request, body: dict[str, Any]) -> dict[str, Any]:
    """Receive messages for an agent."""
    recipient = body.get("recipient")
    msg_type = body.get("type")
    since = body.get("since")

    if not recipient:
        raise HTTPException(status_code=400, detail="recipient required")

    all_messages = await _dequeue_for_recipient(recipient)
    messages: list[dict[str, Any]] = []
    for msg in all_messages:
        if msg.get("recipient") not in (recipient, "*") and msg.get("type") != "broadcast":
            continue
        if msg_type and msg.get("type") != msg_type:
            continue
        if since and msg.get("timestamp", "") < since:
            continue
        messages.append(msg)

    for msg in messages:
        if msg.get("status") == "pending":
            msg["status"] = "delivered"
            await _mark_delivered(msg.get("id", ""))

    return {"messages": messages, "count": len(messages)}


@router.get("/agents")
async def a2a_list_agents(request: Request) -> dict[str, Any]:
    """List discoverable agents."""
    from core.agent_store import AgentStore

    store = AgentStore()
    agents = store.list_agents()
    result = [
        {
            "id": agent["id"],
            "name": agent.get("name", agent["id"]),
            "description": agent.get("description", ""),
            "skills": agent.get("skills", []),
            "tools": agent.get("tools", []),
            "capabilities": ["text", "tools", "skills"],
        }
        for agent in agents
    ]
    return {"agents": result, "count": len(result)}


@router.post("/broadcast")
async def a2a_broadcast(request: Request, msg: A2AMessage) -> dict[str, str]:
    """Broadcast a message to all agents."""
    message_id = f"a2a-broadcast-{uuid.uuid4().hex[:12]}"
    broadcast_msg = A2AMessage(
        sender=msg.sender,
        recipient="*",
        type="broadcast",
        content=msg.content,
        task_id=msg.task_id or message_id,
        skills=msg.skills,
        tools=msg.tools,
        ttl=msg.ttl,
    )
    message = _build_message(broadcast_msg, message_id=message_id, msg_type="broadcast")
    await _enqueue(message)
    return {
        "message_id": message_id,
        "status": "broadcast",
        "timestamp": message["timestamp"],
    }
