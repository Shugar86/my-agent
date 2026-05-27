"""Tests for A2A queue destructive dequeue."""
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from web import a2a_server


@pytest.fixture(autouse=True)
def reset_memory_queue():
    a2a_server._memory_queue.clear()
    yield
    a2a_server._memory_queue.clear()


@pytest.mark.asyncio
async def test_memory_dequeue_removes_messages():
    """Memory fallback removes delivered messages on dequeue."""
    a2a_server._memory_queue.extend([
        {
            "id": "1",
            "recipient": "agent-a",
            "type": "request",
            "content": "hi",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        },
        {
            "id": "2",
            "recipient": "agent-b",
            "type": "request",
            "content": "other",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        },
    ])

    with patch.object(a2a_server.redis_client, "ping", new=AsyncMock(return_value=False)):
        first = await a2a_server._dequeue_for_recipient("agent-a")
        second = await a2a_server._dequeue_for_recipient("agent-a")

    assert len(first) == 1
    assert first[0]["id"] == "1"
    assert second == []
    assert len(a2a_server._memory_queue) == 1
    assert a2a_server._memory_queue[0]["id"] == "2"


@pytest.mark.asyncio
async def test_redis_dequeue_pops_messages():
    """Redis path uses queue_pop instead of non-destructive range."""
    msg_a = json.dumps({
        "id": "1",
        "recipient": "agent-a",
        "type": "request",
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    })
    msg_b = json.dumps({
        "id": "2",
        "recipient": "agent-a",
        "type": "response",
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    })

    pop_results = [msg_a, msg_b, None] + [None] * 400
    pop_mock = AsyncMock(side_effect=pop_results)

    with patch.object(a2a_server.redis_client, "ping", new=AsyncMock(return_value=True)), \
         patch.object(a2a_server.redis_client, "queue_pop", new=pop_mock):
        first = await a2a_server._dequeue_for_recipient("agent-a")
        second = await a2a_server._dequeue_for_recipient("agent-a")

    assert len(first) == 2
    assert second == []


@pytest.mark.asyncio
async def test_expired_message_skipped():
    """Messages past expires_at are not returned."""
    a2a_server._memory_queue.append({
        "id": "old",
        "recipient": "agent-a",
        "type": "request",
        "content": "stale",
        "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    })

    with patch.object(a2a_server.redis_client, "ping", new=AsyncMock(return_value=False)):
        messages = await a2a_server._dequeue_for_recipient("agent-a")

    assert messages == []
    assert a2a_server._memory_queue == []


@pytest.mark.asyncio
async def test_broadcast_fanout_per_agent():
    """Broadcast enqueues per-agent copies instead of shared re-push queue."""
    message = {
        "id": "b1",
        "sender": "hub",
        "recipient": "*",
        "type": "broadcast",
        "content": "hello all",
        "ttl": 3600,
        "expires_at": a2a_server._expires_at_iso(3600),
        "timestamp": a2a_server._now_iso(),
        "status": "pending",
    }
    push_mock = AsyncMock(return_value=True)

    with patch.object(a2a_server, "_list_agent_ids", return_value=["agent-a", "agent-b"]), \
         patch.object(a2a_server.redis_client, "queue_push", new=push_mock):
        await a2a_server._fanout_broadcast(message)

    assert push_mock.await_count == 2
    keys = [call.args[0] for call in push_mock.await_args_list]
    assert "a2a:queue:agent-a" in keys
    assert "a2a:queue:agent-b" in keys
