"""Tests for A2A queue destructive dequeue."""
import json
from unittest.mock import AsyncMock, patch

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
        {"id": "1", "recipient": "agent-a", "type": "request", "content": "hi"},
        {"id": "2", "recipient": "agent-b", "type": "request", "content": "other"},
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
    msg_a = json.dumps({"id": "1", "recipient": "agent-a", "type": "request"})
    msg_b = json.dumps({"id": "2", "recipient": "agent-a", "type": "response"})

    pop_results = [msg_a, msg_b, None] + [None] * 400
    pop_mock = AsyncMock(side_effect=pop_results)

    with patch.object(a2a_server.redis_client, "ping", new=AsyncMock(return_value=True)), \
         patch.object(a2a_server.redis_client, "queue_pop", new=pop_mock):
        first = await a2a_server._dequeue_for_recipient("agent-a")
        second = await a2a_server._dequeue_for_recipient("agent-a")

    assert len(first) == 2
    assert second == []
