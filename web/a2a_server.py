"""A2A (Agent-to-Agent) Protocol endpoints backed by Redis queue."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
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
A2A_BROADCAST_KEY = "a2a:broadcast"


class A2AMessage(BaseModel):
    sender: str
    recipient: str
    type: str = "request"
    content: str
    task_id: str | None = None
    skills: list[str] | None = None
    tools: list[str] | None = None
    ttl: int = 3600


def _queue_key(recipient: str) -> str:
    return f"{A2A_QUEUE_PREFIX}{recipient}"


async def _enqueue(message: dict[str, Any]) -> None:
    global _memory_queue
    payload = json.dumps(message, ensure_ascii=False)
    if message.get("type") == "broadcast" or message.get("recipient") == "*":
        pushed = await redis_client.queue_push(A2A_BROADCAST_KEY, payload)
        if not pushed:
            _memory_queue.append(message)
            if len(_memory_queue) > _MEMORY_QUEUE_MAX:
                _memory_queue = _memory_queue[-_MEMORY_QUEUE_MAX:]
        return
    recipient = message.get("recipient", "")
    pushed = await redis_client.queue_push(_queue_key(recipient), payload)
    if not pushed:
        _memory_queue.append(message)
        if len(_memory_queue) > _MEMORY_QUEUE_MAX:
            _memory_queue = _memory_queue[-_MEMORY_QUEUE_MAX:]


def _message_matches_recipient(msg: dict[str, Any], recipient: str) -> bool:
    return msg.get("recipient") in (recipient, "*") or msg.get("type") == "broadcast"


async def _pop_from_redis_key(key: str, recipient: str, max_items: int = 200) -> list[dict[str, Any]]:
    """Destructively pop messages from a Redis queue key."""
    messages: list[dict[str, Any]] = []
    is_broadcast_key = key == A2A_BROADCAST_KEY

    for _ in range(max_items):
        raw = await redis_client.queue_pop(key)
        if raw is None:
            break
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if is_broadcast_key and not _message_matches_recipient(msg, recipient):
            await redis_client.queue_push(key, raw)
            continue
        messages.append(msg)
    return messages


async def _dequeue_for_recipient(recipient: str) -> list[dict[str, Any]]:
    global _memory_queue
    keys = [_queue_key(recipient), A2A_BROADCAST_KEY]
    messages: list[dict[str, Any]] = []

    if await redis_client.ping():
        for key in keys:
            messages.extend(await _pop_from_redis_key(key, recipient))
        return messages

    kept: list[dict[str, Any]] = []
    for msg in _memory_queue:
        if _message_matches_recipient(msg, recipient):
            messages.append(msg)
        else:
            kept.append(msg)
    _memory_queue = kept
    return messages


@router.post("/send")
async def a2a_send(request: Request, msg: A2AMessage) -> dict[str, str]:
    """Send a message to another agent."""
    message_id = f"a2a-{uuid.uuid4().hex[:12]}"
    message: dict[str, Any] = {
        "id": message_id,
        "sender": msg.sender,
        "recipient": msg.recipient,
        "type": msg.type,
        "content": msg.content,
        "task_id": msg.task_id or message_id,
        "skills": msg.skills or [],
        "tools": msg.tools or [],
        "ttl": msg.ttl,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
    }

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
                    "timestamp": datetime.utcnow().isoformat(),
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
        if msg.get("ttl", 3600) <= 0:
            continue
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
    message = {
        "id": message_id,
        "sender": msg.sender,
        "recipient": "*",
        "type": "broadcast",
        "content": msg.content,
        "task_id": msg.task_id or message_id,
        "skills": msg.skills or [],
        "tools": msg.tools or [],
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
    }
    await _enqueue(message)
    return {
        "message_id": message_id,
        "status": "broadcast",
        "timestamp": message["timestamp"],
    }
