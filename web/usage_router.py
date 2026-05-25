"""Usage analytics API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from core.teams.permissions import require_team_role
from core.usage.tracker import usage_tracker

router = APIRouter(tags=["usage"])


@router.get("/api/usage/summary")
async def usage_summary(
    request: Request,
    team_id: str | None = Query(None),
    period: str = Query("7d"),
):
    """Aggregate usage for a team workspace."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    tid = team_id or getattr(request.state, "workspace_id", None)
    if not tid:
        raise HTTPException(status_code=400, detail="team_id required")
    require_team_role(tid, user_id, "member")
    days = 7 if period == "7d" else 30 if period == "30d" else 7
    return usage_tracker.summary(tid, period_days=days)


@router.post("/api/usage/event")
async def track_ux_event(request: Request):
    """Record a UX analytics event (onboarding, chat, etc.)."""
    user_id = getattr(request.state, "user_id", None)
    workspace_id = getattr(request.state, "workspace_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    body = await request.json()
    event_type = body.get("event_type", "ux_event")
    metadata = body.get("metadata") or {}
    usage_tracker.track(
        event_type,
        team_id=workspace_id,
        user_id=user_id,
        metadata=metadata,
    )
    return {"ok": True}


@router.get("/api/usage/events")
async def usage_events(
    request: Request,
    team_id: str | None = Query(None),
    limit: int = Query(50, le=200),
):
    """List recent usage events."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    tid = team_id or getattr(request.state, "workspace_id", None)
    if not tid:
        raise HTTPException(status_code=400, detail="team_id required")
    require_team_role(tid, user_id, "member")
    return {"events": usage_tracker.list_events(tid, limit=limit)}


@router.get("/api/cost")
async def get_cost_legacy(request: Request):
    """Legacy cost endpoint backed by usage ledger."""
    user_id = getattr(request.state, "user_id", None)
    workspace_id = getattr(request.state, "workspace_id", None)
    if not user_id or not workspace_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    summary = usage_tracker.summary(workspace_id, period_days=30)
    return {
        "session_cost": {
            "tokens": summary["total_tokens"],
            "cost": summary["total_cost_usd"],
        },
        "workspace_id": workspace_id,
    }
