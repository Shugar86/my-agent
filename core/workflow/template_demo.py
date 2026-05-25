"""Mock demo runs for marketplace templates (no integration credentials required)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_template_demo_run(template: dict[str, Any]) -> dict[str, Any]:
    """Build a prerecorded successful run from template definition nodes."""
    definition = template.get("definition") or {}
    nodes = definition.get("nodes") or []
    run_id = f"demo_{uuid.uuid4().hex[:12]}"
    logs: list[dict[str, Any]] = []
    for node in nodes[:12]:
        node_id = node.get("id", "n1")
        node_type = node.get("type", "unknown")
        logs.append({
            "node_id": node_id,
            "event": "started",
            "detail": node_type,
            "timestamp": _now_iso(),
        })
        logs.append({
            "node_id": node_id,
            "event": "completed",
            "detail": {"mock": True, "type": node_type},
            "timestamp": _now_iso(),
        })
    if not logs:
        logs = [{
            "node_id": "demo",
            "event": "completed",
            "detail": "Empty template preview",
            "timestamp": _now_iso(),
        }]
    return {
        "success": True,
        "run_id": run_id,
        "status": "success",
        "mode": "mock",
        "template_id": template.get("id"),
        "logs": logs,
        "message": "Демо-запуск без интеграций — показывает типичный flow шаблона.",
    }
