"""Node handler registry for workflow engine."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from core.workflow.models import RunContext

NodeHandler = Callable[[RunContext, dict[str, Any]], Awaitable[dict[str, Any]]]

_handlers: dict[str, NodeHandler] = {}


def register_node_handler(node_type: str, handler: NodeHandler) -> None:
    """Register a handler for a workflow node type."""
    _handlers[node_type] = handler


def get_node_handler(node_type: str) -> NodeHandler | None:
    """Return handler for node type or None."""
    return _handlers.get(node_type)


def reset_registry() -> None:
    """Clear all handlers (for tests)."""
    _handlers.clear()


def list_node_types() -> list[str]:
    """Return all registered node types."""
    return sorted(_handlers.keys())
