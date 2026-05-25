"""Chat sessions REST API."""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.state_db import StateDB

router = APIRouter(tags=["sessions"])
state_db = StateDB(os.environ.get("STATE_DB_PATH", "data/state.db"))


def _full_session_id(user_id: str, raw_id: str) -> str:
    """Build scoped session id for a user."""
    return f"{user_id}::{raw_id}"


def _assert_session_owner(user_id: str, full_id: str) -> None:
    """Ensure session belongs to the authenticated user."""
    if not full_id.startswith(f"{user_id}::"):
        raise HTTPException(status_code=403, detail="Forbidden")


class SessionCreateRequest(BaseModel):
    """Create a new chat session."""

    title: str = "New chat"
    agent_id: str = "universal"


@router.get("/api/sessions")
async def list_sessions(request: Request):
    """List chat sessions for the current user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    sessions = state_db.list_sessions_for_user(user_id)
    return {
        "sessions": [
            {
                "id": s["id"].split("::", 1)[-1] if "::" in s["id"] else s["id"],
                "full_id": s["id"],
                "title": s.get("title") or "New chat",
                "message_count": s.get("message_count", 0),
                "started_at": s.get("started_at"),
            }
            for s in sessions
        ],
        "total": len(sessions),
    }


@router.post("/api/sessions")
async def create_session(request: Request, body: SessionCreateRequest):
    """Create a new chat session."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    raw_id = f"s_{uuid.uuid4().hex[:12]}"
    full_id = _full_session_id(user_id, raw_id)
    state_db.create_session(full_id, source="web", user_id=user_id, model=body.agent_id)
    if body.title:
        state_db.set_session_title(full_id, body.title)
    return {"id": raw_id, "full_id": full_id, "title": body.title}


@router.get("/api/sessions/{session_id}/messages")
async def get_session_messages(request: Request, session_id: str):
    """Get messages for a chat session."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    full_id = _full_session_id(user_id, session_id)
    _assert_session_owner(user_id, full_id)
    if not state_db.get_session(full_id):
        raise HTTPException(status_code=404, detail="Session not found")
    rows = state_db.get_messages(full_id)
    messages = [
        {"role": r["role"], "content": r.get("content") or ""}
        for r in rows
        if r["role"] in ("user", "assistant") and r.get("content")
    ]
    return {"session_id": session_id, "messages": messages}


@router.delete("/api/sessions/{session_id}")
async def delete_session(request: Request, session_id: str):
    """Delete a chat session."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    full_id = _full_session_id(user_id, session_id)
    _assert_session_owner(user_id, full_id)
    if not state_db.get_session(full_id):
        raise HTTPException(status_code=404, detail="Session not found")
    state_db.delete_session(full_id)
    return {"success": True}
