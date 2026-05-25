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


@dataclass
class WorkflowNode:
    """Single node in a workflow graph."""

    id: str
    type: str
    config: dict[str, Any] = field(default_factory=dict)
    position: dict[str, float] | None = None


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

    def resolve_template(self, value: str) -> str:
        """Replace {{node_id.field}} placeholders in strings."""
        if not isinstance(value, str) or "{{" not in value:
            return value
        result = value
        for node_id, output in self.node_outputs.items():
            if isinstance(output, dict):
                for key, val in output.items():
                    result = result.replace(f"{{{{{node_id}.{key}}}}}", str(val))
                if "output" in output:
                    result = result.replace(f"{{{{{node_id}.output}}}}", str(output["output"]))
            else:
                result = result.replace(f"{{{{{node_id}.output}}}}", str(output))
        if "trigger" in self.node_outputs:
            trigger = self.node_outputs["trigger"]
            if isinstance(trigger, dict):
                for key, val in trigger.items():
                    result = result.replace(f"{{{{trigger.{key}}}}}", str(val))
        if self.trigger_payload:
            for key, val in self.trigger_payload.items():
                result = result.replace(f"{{{{trigger.{key}}}}}", str(val))
        for key, val in self.state.items():
            result = result.replace(f"{{{{state.{key}}}}}", str(val))
        return result

    def resolve_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Resolve templates in node config values."""
        resolved: dict[str, Any] = {}
        for key, val in config.items():
            if isinstance(val, str):
                resolved[key] = self.resolve_template(val)
            else:
                resolved[key] = val
        return resolved

    def log(self, node_id: str, event: str, detail: Any = None) -> None:
        """Append execution log entry."""
        self.logs.append({"node_id": node_id, "event": event, "detail": detail})
