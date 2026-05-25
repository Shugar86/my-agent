"""Tests for WebSocket chat endpoint."""
import pytest
import json
import asyncio

pytestmark = pytest.mark.asyncio


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.accepted = False
        self.sent = []
        self.received = []
        self.closed = False
        self._msg_processed = asyncio.Event()

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        self.sent.append(data)
        if data.get("type") in ("done", "error"):
            self._msg_processed.set()

    async def receive_json(self):
        if self.received:
            msg = self.received.pop(0)
            # If no more messages after this, wait for processing
            if not self.received:
                # Wait for background task to complete or timeout
                try:
                    await asyncio.wait_for(self._msg_processed.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    pass
            return msg
        raise Exception("No more messages")

    async def receive_text(self):
        return ""

    async def close(self):
        self.closed = True


@pytest.fixture
def mock_ws():
    return MockWebSocket()


async def test_websocket_chat_disconnect(mock_ws):
    """Test WebSocket gracefully handles immediate disconnect."""
    from web.server import websocket_chat

    # No messages - immediate disconnect
    try:
        await websocket_chat(mock_ws)
    except Exception:
        pass

    assert mock_ws.accepted


async def test_websocket_cancel(mock_ws):
    """Test WebSocket cancel message."""
    from web.server import websocket_chat

    mock_ws.received = [
        {"type": "cancel"},
    ]

    try:
        await websocket_chat(mock_ws)
    except Exception:
        pass

    assert mock_ws.accepted
    cancel_msgs = [s for s in mock_ws.sent if s["type"] == "cancelled"]
    assert len(cancel_msgs) > 0


async def test_websocket_unknown_type(mock_ws):
    """Test WebSocket handles unknown message type."""
    from web.server import websocket_chat

    mock_ws.received = [
        {"type": "unknown_command"},
    ]

    try:
        await websocket_chat(mock_ws)
    except Exception:
        pass

    assert mock_ws.accepted
    error_msgs = [s for s in mock_ws.sent if s["type"] == "error"]
    assert len(error_msgs) > 0
    assert "Unknown type" in error_msgs[0]["message"]


async def test_websocket_empty_message(mock_ws):
    """Test WebSocket handles empty message."""
    from web.server import websocket_chat

    mock_ws.received = [
        {"type": "ask", "message": ""},
    ]

    try:
        await websocket_chat(mock_ws)
    except Exception:
        pass

    assert mock_ws.accepted
    error_msgs = [s for s in mock_ws.sent if s["type"] == "error"]
    assert len(error_msgs) > 0
    assert "Empty" in error_msgs[0]["message"]
