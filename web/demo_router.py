"""Investor demo endpoints.

Exposes a single ``POST /api/demo/run`` that always returns a believable run,
even when API keys (OpenRouter / Tavily / etc.) are not configured. The route:

1. Looks up the ``tpl_competitor_intelligence`` template; auto-installs it for
   the current user if missing.
2. Streams a prerecorded log timeline (`data/demo/competitor_run_sample.json`)
   into the run record so the existing run viewer + ``ExecutionTimeline``
   render the demo without any custom UI changes.
3. Serves the prebuilt DOCX artifact via ``GET /api/demo/artifact/{filename}``.

Trade-off: a separate router (vs adding to ``workflow_router.py``) keeps demo
code isolated — easy to disable for production, easy to remove post-fundraise.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.workflow.executor import WorkflowExecutor
from core.workflow.store import workflow_store

logger = logging.getLogger(__name__)
router = APIRouter(tags=["demo"])
executor = WorkflowExecutor()

DEMO_DIR = Path("data/demo")
DEMO_TEMPLATE_ID = "tpl_competitor_intelligence"
DEMO_SAMPLE_FILE = DEMO_DIR / "competitor_run_sample.json"

# Trade-off: we check a single env var as a "real keys present" signal.
# Adjust here if the project switches LLM provider.
REAL_MODE_ENV = "OPENROUTER_API_KEY"


class DemoRunRequest(BaseModel):
    """Request body for the 90-second demo."""

    target: str = "Notion"
    our_company: str = "Linear"
    real: bool = False


def _load_sample() -> dict[str, Any]:
    """Load the prerecorded run sample."""
    if not DEMO_SAMPLE_FILE.exists():
        raise FileNotFoundError(f"Demo sample missing: {DEMO_SAMPLE_FILE}")
    return json.loads(DEMO_SAMPLE_FILE.read_text(encoding="utf-8"))


def _ensure_template_installed(
    user_id: str | None, workspace_id: str | None
) -> dict[str, Any] | None:
    """Return existing competitor workflow for the user, install if absent.

    Returns the workflow dict or ``None`` if the template itself is missing
    (seed not yet run).
    """
    workflows = workflow_store.list_workflows(workspace_id=workspace_id) if workspace_id \
        else workflow_store.list_workflows(owner_id=user_id)
    for wf in workflows:
        if (wf.get("name") or "").lower().startswith("competitor intelligence"):
            return wf

    template = workflow_store.get_template(DEMO_TEMPLATE_ID)
    if not template:
        logger.warning("Demo template %s not found — run seed_workflow_templates.py", DEMO_TEMPLATE_ID)
        return None
    return workflow_store.clone_template(
        DEMO_TEMPLATE_ID, owner_id=user_id, workspace_id=workspace_id
    )


async def _stream_mock_logs(run_id: str, sample: dict[str, Any], target: str) -> None:
    """Replay prerecorded log events into a workflow run with realtime delays.

    The frontend polls ``GET /api/workflows/{wf_id}/runs/{run_id}`` so writing
    to the same ``workflow_runs`` table makes the existing UI light up nodes
    one-by-one without any extra wiring.
    """
    logs: list[dict[str, Any]] = []
    try:
        for event in sample.get("events", []):
            await asyncio.sleep(max(50, int(event.get("delay_ms", 200))) / 1000.0)
            entry = {
                "node_id": event.get("node_id"),
                "event": event.get("event"),
                "detail": event.get("detail", {}),
            }
            # Personalise output so the demo references the entered company.
            detail = entry["detail"]
            if isinstance(detail, dict):
                summary = detail.get("output", {}).get("summary") if isinstance(detail.get("output"), dict) else None
                if isinstance(summary, str) and "Notion" in summary and target != "Notion":
                    detail["output"]["summary"] = summary.replace("Notion", target)
            logs.append(entry)
            workflow_store.update_run_logs(run_id, logs, status="running")
        workflow_store.finish_run(run_id, "success", logs)
    except (RuntimeError, OSError) as exc:
        logger.warning("Demo log stream failed: %s", exc)
        workflow_store.finish_run(run_id, "failed", logs + [{"event": "error", "detail": str(exc)}])


@router.post("/api/demo/run")
async def start_demo_run(
    request: Request,
    body: DemoRunRequest,
    background: BackgroundTasks,
) -> dict[str, Any]:
    """Start a 90-second demo run.

    Real mode is used when ``body.real=True`` AND the LLM API key is configured.
    Otherwise we fall back to the prerecorded mock — guarantees the demo never
    breaks in front of an investor.
    """
    user_id = getattr(request.state, "user_id", None)
    workspace_id = getattr(request.state, "workspace_id", None)

    workflow = _ensure_template_installed(user_id, workspace_id)
    if not workflow:
        raise HTTPException(
            status_code=503,
            detail="Demo template not seeded. Run scripts/seed_workflow_templates.py.",
        )

    payload = {"target": body.target, "our_company": body.our_company}
    keys_available = bool(os.getenv(REAL_MODE_ENV))

    if body.real and keys_available:
        result = await executor.run(
            workflow["id"], trigger_payload=payload, user_id=user_id
        )
        return {
            "mode": "real",
            "workflow_id": workflow["id"],
            "run_id": result.get("run_id"),
            "success": result.get("success", False),
            "artifact_url": "/api/demo/artifact/competitor_brief_notion_vs_linear.docx",
        }

    sample = _load_sample()
    run = workflow_store.create_run(workflow["id"])
    background.add_task(_stream_mock_logs, run["id"], sample, body.target)
    return {
        "mode": "mock",
        "workflow_id": workflow["id"],
        "run_id": run["id"],
        "expected_duration_ms": sample.get("summary", {}).get("total_duration_ms", 30000),
        "artifact_url": "/api/demo/artifact/competitor_brief_notion_vs_linear.docx",
        "summary": sample.get("summary", {}),
    }


@router.get("/api/demo/artifact/{filename}")
async def download_demo_artifact(filename: str) -> FileResponse:
    """Serve a prebuilt artifact (DOCX/PDF) from the demo directory."""
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = DEMO_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
        if filename.endswith(".docx") else "application/octet-stream"
    return FileResponse(path, media_type=media, filename=filename)


@router.get("/api/demo/sample")
async def demo_sample() -> dict[str, Any]:
    """Return the demo summary (used by Dashboard hero for ROI metrics)."""
    sample = _load_sample()
    return {
        "summary": sample.get("summary", {}),
        "node_order": sample.get("node_order", []),
        "default_payload": sample.get("default_payload", {}),
    }
