"""Utility node handlers: Set, Merge, Wait, Code (sandboxed).

These nodes give workflows the n8n-like building blocks for data shaping
and small pieces of in-line logic without leaving the visual editor.

Trade-offs:
    - ``util.code`` runs Python in a restricted ``exec`` sandbox. It is **not**
      safe against a fully malicious operator with shell access, but it blocks
      ``import``, file I/O, and most globals — sufficient for trusted-tenant
      B2B usage. For multi-tenant SaaS we should swap to a subprocess +
      seccomp jail (post-v3.0 backlog).
    - ``util.wait`` uses ``asyncio.sleep`` with an upper bound (default 5
      minutes) so a runaway workflow cannot hold a worker indefinitely.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.workflow.models import RunContext
from core.workflow.registry import register_node_handler

logger = logging.getLogger(__name__)

_MAX_WAIT_SECONDS = 300
_CODE_TIMEOUT_SECONDS = 5


async def handle_util_set(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Materialize a dict of values from templated config.

    Config:
        values (dict): keys/expressions to compute.
        store (str): optional state key to persist the result under.

    Returns:
        ``{"output": <dict>, "success": True}``.
    """
    resolved = ctx.resolve_config(config)
    values = resolved.get("values") or {}
    if not isinstance(values, dict):
        return {"output": {}, "success": False, "error": "values must be a dict"}
    store_key = resolved.get("store")
    if isinstance(store_key, str) and store_key:
        ctx.state[store_key] = values
    return {"output": values, "success": True, **values}


async def handle_util_merge(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Merge outputs from multiple upstream nodes into one dict.

    Config:
        sources (list[str]): node ids whose ``output`` should be merged.
                             If omitted, merges all upstream node outputs.
        strategy (str): "shallow" (default) or "deep".
    """
    resolved = ctx.resolve_config(config)
    sources = resolved.get("sources")
    strategy = (resolved.get("strategy") or "shallow").lower()

    if not sources:
        sources = [k for k in ctx.node_outputs.keys() if k != "trigger"]

    merged: dict[str, Any] = {}
    for src in sources:
        out = ctx.node_outputs.get(src)
        payload = out.get("output") if isinstance(out, dict) else out
        if isinstance(payload, dict):
            if strategy == "deep":
                _deep_merge(merged, payload)
            else:
                merged.update(payload)
        elif payload is not None:
            merged[src] = payload
    return {"output": merged, "success": True}


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, val in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(val, dict):
            _deep_merge(target[key], val)
        else:
            target[key] = val


async def handle_util_wait(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Pause the workflow for ``seconds`` (max 300s)."""
    resolved = ctx.resolve_config(config)
    try:
        seconds = float(resolved.get("seconds", 1))
    except (TypeError, ValueError):
        seconds = 1.0
    seconds = max(0.0, min(seconds, _MAX_WAIT_SECONDS))
    await asyncio.sleep(seconds)
    return {"output": {"waited_seconds": seconds}, "success": True}


async def handle_util_code(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Execute a small Python snippet in a restricted sandbox.

    The script may set ``output`` (any JSON-serializable value) which becomes
    the node's output. Available locals: ``trigger`` (payload), ``state``
    (mutable), ``nodes`` (read-only dict of node outputs).

    Restrictions:
        - No ``import``, ``open``, ``__import__``, ``compile``, ``exec``.
        - 5-second timeout via ``asyncio.wait_for``.
    """
    resolved = ctx.resolve_config(config)
    script = resolved.get("script") or resolved.get("code") or ""
    if not isinstance(script, str) or not script.strip():
        return {"output": None, "success": True}

    forbidden = ("import ", "__import__", "open(", "exec(", "eval(", "compile(", "globals(", "subprocess")
    lower = script.lower()
    for token in forbidden:
        if token in lower:
            return {"output": None, "success": False, "error": f"Forbidden token: {token.strip()}"}

    safe_globals: dict[str, Any] = {
        "__builtins__": {
            "len": len, "range": range, "min": min, "max": max, "sum": sum,
            "abs": abs, "round": round, "sorted": sorted, "reversed": reversed,
            "str": str, "int": int, "float": float, "bool": bool, "list": list,
            "dict": dict, "tuple": tuple, "set": set, "any": any, "all": all,
            "enumerate": enumerate, "zip": zip, "print": lambda *a, **k: None,
        }
    }
    locals_dict: dict[str, Any] = {
        "trigger": ctx.trigger_payload,
        "state": ctx.state,
        "nodes": dict(ctx.node_outputs),
        "output": None,
    }

    try:
        await asyncio.wait_for(
            asyncio.to_thread(_exec_sandboxed, script, safe_globals, locals_dict),
            timeout=_CODE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return {"output": None, "success": False, "error": "Code timed out"}
    except Exception as exc:  # noqa: BLE001 — user code may raise anything
        logger.warning("util.code failed: %s", exc)
        return {"output": None, "success": False, "error": str(exc)}

    return {"output": locals_dict.get("output"), "success": True}


def _exec_sandboxed(script: str, globs: dict[str, Any], locs: dict[str, Any]) -> None:
    """Run user script with restricted builtins.

    NOTE: ``exec`` is intentional here. The threat model is "trusted operator,
    untrusted typo" — we strip imports and dangerous builtins. See module
    docstring for the multi-tenant upgrade path.
    """
    exec(script, globs, locs)  # noqa: S102 — sandboxed by design


def register_util_handlers() -> None:
    """Register utility node handlers."""
    register_node_handler("util.set", handle_util_set)
    register_node_handler("util.merge", handle_util_merge)
    register_node_handler("util.wait", handle_util_wait)
    register_node_handler("util.code", handle_util_code)
