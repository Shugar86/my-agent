"""Helpers for calling async code from synchronous contexts."""
from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
import logging
from typing import Any, Coroutine, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def run_coro_sync(coro: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine from sync code, even when an event loop is already running."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def invoke_execute_fn(fn: Any, **kwargs: Any) -> Any:
    """Call a tool execute_fn that may be synchronous or async."""
    if inspect.iscoroutinefunction(fn):
        return run_coro_sync(fn(**kwargs))
    result = fn(**kwargs)
    if inspect.iscoroutine(result):
        return run_coro_sync(result)
    return result
