"""Condition node handler."""

from __future__ import annotations

import re
from typing import Any

from core.workflow.models import RunContext
from core.workflow.registry import register_node_handler


async def handle_condition(ctx: RunContext, config: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a simple condition expression.

    Supports:
      - field + operator + value (e.g. field=output, operator=contains, value=error)
      - expression string with {{node.field}} resolved
    """
    resolved = ctx.resolve_config(config)
    field = resolved.get("field", "output")
    operator = resolved.get("operator", "equals")
    expected = str(resolved.get("value", ""))

    source_node = resolved.get("source_node", "")
    actual = ""
    if source_node and source_node in ctx.node_outputs:
        node_out = ctx.node_outputs[source_node]
        if isinstance(node_out, dict):
            actual = str(node_out.get(field, node_out.get("output", "")))
        else:
            actual = str(node_out)
    elif "expression" in resolved:
        actual = ctx.resolve_template(resolved["expression"])
    else:
        actual = expected if operator == "equals" else ""

    result = _evaluate(actual, operator, expected)
    return {"output": result, "branch": "true" if result else "false", "actual": actual}


def _evaluate(actual: str, operator: str, expected: str) -> bool:
    if operator == "equals":
        return actual == expected
    if operator == "contains":
        return expected.lower() in actual.lower()
    if operator == "not_empty":
        return bool(actual.strip())
    if operator == "regex":
        return bool(re.search(expected, actual))
    return bool(actual)


def register_condition_handlers() -> None:
    """Register condition node handlers."""
    register_node_handler("condition", handle_condition)
