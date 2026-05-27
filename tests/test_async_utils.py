"""Tests for async/sync bridge helpers."""
import asyncio

import pytest

from core.async_utils import invoke_execute_fn, run_coro_sync
from core.tool_registry import ToolRegistry


@pytest.mark.asyncio
async def test_run_coro_sync_from_running_loop():
    async def sample() -> str:
        return "ok"

    assert run_coro_sync(sample()) == "ok"


def test_invoke_execute_fn_async():
    async def async_tool(**kwargs):
        return kwargs["x"] + 1

    assert invoke_execute_fn(async_tool, x=41) == 42


def test_tool_registry_executes_async_fn():
    reg = ToolRegistry()

    async def async_tool(value: str = "") -> str:
        return f"async:{value}"

    reg.register(
        name="async_echo",
        description="async test tool",
        parameters={"type": "object", "properties": {"value": {"type": "string"}}},
        execute_fn=async_tool,
    )
    assert reg.execute("async_echo", value="hi") == "async:hi"
