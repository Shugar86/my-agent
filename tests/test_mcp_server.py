"""Tests for MCP server tool execution."""
import pytest

from web.mcp_server import _call_tool


@pytest.mark.asyncio
async def test_call_tool_uses_execute_key():
    """MCP _call_tool reads the execute handler from tool registry metadata."""
    from core.tool_registry import registry

    def echo_tool(message: str = "hi") -> dict:
        return {"message": message}

    registry.register(
        name="test_mcp_echo",
        description="Echo test tool",
        parameters={"type": "object", "properties": {"message": {"type": "string"}}},
        execute_fn=echo_tool,
    )
    try:
        result = await _call_tool("test_mcp_echo", {"message": "hello"})
        assert result["isError"] is False
        assert "hello" in result["content"][0]["text"]
    finally:
        registry.unregister("test_mcp_echo")


@pytest.mark.asyncio
async def test_call_tool_missing_tool_raises():
    """Unknown tool name raises MCPError."""
    from web.mcp_server import MCPError

    with pytest.raises(MCPError) as exc_info:
        await _call_tool("nonexistent_tool_xyz", {})
    assert exc_info.value.code == MCPError.METHOD_NOT_FOUND
