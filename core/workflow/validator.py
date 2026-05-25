"""Workflow definition validation."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from core.workflow.models import WorkflowDefinition
from core.workflow.registry import get_node_handler


def validate_workflow(definition: WorkflowDefinition) -> dict[str, Any]:
    """Validate workflow graph structure and node configs.

    Returns:
        dict with keys: valid (bool), errors (list[str]), warnings (list[str])
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not definition.nodes:
        errors.append("Workflow has no nodes")
        return {"valid": False, "errors": errors, "warnings": warnings}

    node_ids = {n.id for n in definition.nodes}
    for edge in definition.edges:
        if edge.from_node not in node_ids:
            errors.append(f"Edge references unknown source node: {edge.from_node}")
        if edge.to_node not in node_ids:
            errors.append(f"Edge references unknown target node: {edge.to_node}")

    if _has_cycle(definition):
        errors.append("Workflow contains a cycle")

    for node in definition.nodes:
        if not get_node_handler(node.type):
            warnings.append(f"No handler registered for node type: {node.type}")
        if node.type == "trigger.schedule":
            cron = str(node.config.get("cron", "0 9 * * *"))
            parts = cron.split()
            if len(parts) != 5:
                errors.append(f"Invalid cron expression on node {node.id}: '{cron}'")

    orphans = _orphan_nodes(definition)
    for oid in orphans:
        warnings.append(f"Orphan node (no connections): {oid}")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def _has_cycle(definition: WorkflowDefinition) -> bool:
    """Detect cycle via Kahn's algorithm."""
    in_degree: dict[str, int] = defaultdict(int)
    adj: dict[str, list[str]] = defaultdict(list)
    nodes = {n.id for n in definition.nodes}
    for n in nodes:
        in_degree.setdefault(n, 0)
    for edge in definition.edges:
        if edge.from_node in nodes and edge.to_node in nodes:
            adj[edge.from_node].append(edge.to_node)
            in_degree[edge.to_node] += 1
    queue = deque([n for n in nodes if in_degree[n] == 0])
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return visited != len(nodes)


def _orphan_nodes(definition: WorkflowDefinition) -> list[str]:
    """Nodes with no edges."""
    connected: set[str] = set()
    for edge in definition.edges:
        connected.add(edge.from_node)
        connected.add(edge.to_node)
    return [n.id for n in definition.nodes if n.id not in connected and len(definition.nodes) > 1]
