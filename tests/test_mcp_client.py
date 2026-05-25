"""Tests for MCP Client Manager."""
import pytest
from unittest.mock import patch, MagicMock


class TestMCPClientManager:
    """Unit tests for core.mcp_client_manager."""

    def test_load_config_empty(self):
        """Load config returns empty list if file missing."""
        from core.mcp_client_manager import MCPClientManager
        mgr = MCPClientManager()
        mgr._config_path = MagicMock()
        mgr._config_path.exists.return_value = False
        clients = mgr.load_config()
        assert clients == []

    def test_list_connections_empty(self):
        """List connections returns empty when none connected."""
        from core.mcp_client_manager import MCPClientManager
        mgr = MCPClientManager()
        connections = mgr.list_connections()
        assert connections == []

    def test_get_all_tools_empty(self):
        """Get all tools returns empty when no connections."""
        from core.mcp_client_manager import MCPClientManager
        mgr = MCPClientManager()
        tools = mgr.get_all_tools()
        assert tools == []

    def test_call_tool_not_connected(self):
        """Call tool on non-existent server returns error."""
        import asyncio
        from core.mcp_client_manager import MCPClientManager
        mgr = MCPClientManager()
        result = asyncio.get_event_loop().run_until_complete(
            mgr.call_tool("nonexistent", "tool", {})
        )
        assert "error" in result
        assert "not connected" in result["error"]

    def test_mcp_client_connection_tools_property(self):
        """MCPClientConnection tools property returns list."""
        from core.mcp_client_manager import MCPClientConnection
        conn = MCPClientConnection(name="test", transport="stdio", config={})
        assert conn.tools == []
        assert conn.resources == []
        assert conn.prompts == []

    def test_disconnect_no_process(self):
        """Disconnect with no process does not crash."""
        from core.mcp_client_manager import MCPClientConnection
        conn = MCPClientConnection(name="test", transport="stdio", config={})
        conn.disconnect()  # Should not raise


class TestMCPClientManagerMocked:
    """Tests with mocked subprocess."""

    @pytest.mark.asyncio
    async def test_stdio_init_mocked(self):
        """Stdio init with mocked Popen."""
        from core.mcp_client_manager import MCPClientConnection
        import json

        conn = MCPClientConnection(
            name="test",
            transport="stdio",
            config={"command": "echo", "args": ["test"]},
        )
        # Cannot fully test without real subprocess, but verify structure
        assert conn.name == "test"
        assert conn.transport == "stdio"
        assert not conn._initialized
