"""Tests for Real-time Collaboration (WebSocket rooms)."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock


class TestCollaboration:
    """Tests for WebSocket collaboration rooms."""

    @pytest.mark.asyncio
    async def test_room_join_broadcast(self):
        """Joining a room broadcasts system message."""
        from web.server import _collab_rooms, websocket_collaboration

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.receive_json = AsyncMock(side_effect=[
            {"type": "join", "username": "Alice"},
            Exception("disconnect"),  # Force disconnect
        ])
        mock_ws.send_json = AsyncMock()

        # Clear room
        room_id = "test-room-123"
        _collab_rooms[room_id] = [mock_ws]

        try:
            await websocket_collaboration(mock_ws, room_id)
        except Exception:
            pass

        # Verify system message was broadcast
        calls = mock_ws.send_json.call_args_list
        system_calls = [c for c in calls if c.args and c.args[0].get("type") == "system"]
        assert len(system_calls) >= 1
        assert "Alice" in str(system_calls[0].args[0].get("message", ""))

        # Cleanup
        if room_id in _collab_rooms:
            del _collab_rooms[room_id]

    def test_collab_rooms_dict_exists(self):
        """Collaboration rooms dictionary exists."""
        from web.server import _collab_rooms
        assert isinstance(_collab_rooms, dict)

    @pytest.mark.asyncio
    async def test_room_chat_broadcast(self):
        """Chat message in room broadcasts to all."""
        from web.server import _collab_rooms

        ws1 = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json = AsyncMock()

        room_id = "test-chat-room"
        _collab_rooms[room_id] = [ws1, ws2]

        # Simulate broadcast
        from web.server import websocket_collaboration
        ws1.receive_json = AsyncMock(side_effect=[
            {"type": "chat", "message": "Hello", "agent_id": "universal", "auto_agent": False},
            Exception("disconnect"),
        ])

        try:
            await websocket_collaboration(ws1, room_id)
        except Exception:
            pass

        # Verify ws2 received the chat message
        chat_calls = [c for c in ws2.send_json.call_args_list if c.args and c.args[0].get("type") == "chat"]
        assert len(chat_calls) >= 1
        assert "Hello" in str(chat_calls[0].args[0])

        # Cleanup
        if room_id in _collab_rooms:
            del _collab_rooms[room_id]
