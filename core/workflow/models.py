"""Workflow definition models (JSON DAG)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    """Supported workflow node types."""

    TRIGGER_WEBHOOK = "trigger.webhook"
    TRIGGER_SCHEDULE = "trigger.schedule"
    TRIGGER_EMAIL = "trigger.email"
    TRIGGER_TELEGRAM = "trigger.telegram"
    TRIGGER_NEW_LEAD = "trigger.new_lead"
    AGENT_SKILL = "agent.skill"
    CONDITION = "condition"
    ACTION_TELEGRAM = "action.telegram"
    ACTION_SLACK = "action.slack"
    ACTION_GMAIL = "action.gmail_send"
    ACTION_SHEETS_READ = "action.sheets_read"
    ACTION_SHEETS_WRITE = "action.sheets_write"
    ACTION_NOTION_PAGE = "action.notion_page"
    ACTION_NOTION_DB = "action.notion_db_update"
    ACTION_WEBHOOK = "action.webhook"
    ACTION_HTTP = "action.http"
    UTIL_SET = "util.set"
    UTIL_MERGE = "util.merge"
    UTIL_WAIT = "util.wait"
    UTIL_CODE = "util.code"


@dataclass
class RetryPolicy:
    """Per-node retry configuration."""

    max_attempts: int = 1
    backoff_seconds: float = 1.0

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> RetryPolicy:
        """Parse retry policy from node config (``retry`` key)."""
        raw = config.get("retry") or {}
        if isinstance(raw, dict):
            try:
                attempts = max(1, int(raw.get("max_attempts", 1)))
            except (TypeError, ValueError):
                attempts = 1
            try:
                backoff = max(0.0, float(raw.get("backoff_seconds", 1.0)))
            except (TypeError, ValueError):
                backoff = 1.0
            return cls(max_attempts=attempts, backoff_seconds=backoff)
        return cls()


@dataclass
class WorkflowNode:
    """Single node in a workflow graph."""

    id: str
    type: str
    config: dict[str, Any] = field(default_factory=dict)
    position: dict[str, float] | None = None

    @property
    def retry(self) -> RetryPolicy:
        """Retry policy parsed from config."""
        return RetryPolicy.from_config(self.config)

    @property
    def continue_on_error(self) -> bool:
        """If True, downstream error edges are routed instead of failing run."""
        return bool(self.config.get("continue_on_error"))


@dataclass
class WorkflowEdge:
    """Directed edge between nodes."""

    from_node: str
    to_node: str
    label: str | None = None


@dataclass
class WorkflowDefinition:
    """Complete workflow graph definition."""

    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorkflowDefinition:
        """Parse workflow definition from JSON-compatible dict."""
        nodes = [
            WorkflowNode(
                id=n["id"],
                type=n["type"],
                config=n.get("config", {}),
                position=n.get("position"),
            )
            for n in data.get("nodes", [])
        ]
        edges = [
            WorkflowEdge(
                from_node=e.get("from") or e.get("from_node", ""),
                to_node=e.get("to") or e.get("to_node", ""),
                label=e.get("label"),
            )
            for e in data.get("edges", [])
        ]
        return cls(nodes=nodes, edges=edges)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "config": n.config,
                    **({"position": n.position} if n.position else {}),
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "from": e.from_node,
                    "to": e.to_node,
                    **({"label": e.label} if e.label else {}),
                }
                for e in self.edges
            ],
        }

    @classmethod
    def from_json(cls, raw: str) -> WorkflowDefinition:
        """Parse workflow from JSON string."""
        return cls.from_dict(json.loads(raw or "{}"))

    def to_json(self) -> str:
        """Serialize workflow to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class RunContext:
    """Runtime context for workflow execution."""

    run_id: str
    workflow_id: str
    user_id: str | None = None
    trigger_payload: dict[str, Any] = field(default_factory=dict)
    node_outputs: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)

    def _scope(self) -> dict[str, Any]:
        """Build evaluation scope for expression engine.

        Trade-off: rebuilt per call (small cost, always reflects current
        ``node_outputs`` snapshot). Callers typically resolve a node's
        config once before execution.
        """
        scope: dict[str, Any] = dict(self.node_outputs)
        trigger_scope: dict[str, Any] = {}
        if isinstance(self.trigger_payload, dict):
            trigger_scope.update(self.trigger_payload)
        trigger_scope["payload"] = self.trigger_payload
        trigger_node_out = self.node_outputs.get("trigger")
        if isinstance(trigger_node_out, dict):
            trigger_scope.update(trigger_node_out)
        scope["trigger"] = trigger_scope
        scope["state"] = self.state
        scope["env"] = {}
        return scope

    def resolve_template(self, value: Any) -> Any:
        """Render ``{{ ... }}`` expressions in a string (or pass-through).

        Backward compatible: simple ``{{node.field}}`` works as before.
        New: helpers like ``{{ now() }}``, indexing ``a1.items[0]``, and
        type-preserving single-expression returns (for objects/lists).
        """
        from core.workflow.expressions import render_template

        if not isinstance(value, str):
            return value
        return render_template(value, self._scope())

    def resolve_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Resolve templates recursively in node config (strings, dicts, lists)."""
        from core.workflow.expressions import render_template

        scope = self._scope()
        return {key: render_template(val, scope) for key, val in config.items()}

    def log(self, node_id: str, event: str, detail: Any = None) -> None:
        """Append execution log entry."""
        self.logs.append({"node_id": node_id, "event": event, "detail": detail})
