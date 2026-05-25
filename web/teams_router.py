"""Team workspace API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from core.teams.permissions import require_team_role
from core.teams.store import team_store

router = APIRouter(tags=["teams"])


class TeamCreateRequest(BaseModel):
    """Create team request."""

    name: str


class InviteRequest(BaseModel):
    """Invite member by email."""

    email: str
    role: str = "member"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email")
        return v.lower().strip()


class AcceptInviteRequest(BaseModel):
    """Accept team invite."""

    token: str


class MemberRoleUpdate(BaseModel):
    """Update member role."""

    role: str


class ActiveTeamRequest(BaseModel):
    """Switch active workspace."""

    team_id: str


@router.get("/api/teams")
async def list_teams(request: Request):
    """List teams for the current user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    teams = team_store.list_teams_for_user(user_id)
    active = getattr(request.state, "workspace_id", None)
    return {"teams": teams, "active_team_id": active, "total": len(teams)}


@router.post("/api/teams")
async def create_team(request: Request, body: TeamCreateRequest):
    """Create a new team."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Team name required")
    team = team_store.create_team(body.name.strip(), user_id)
    return {"success": True, "team": team}


@router.get("/api/teams/{team_id}/members")
async def list_members(request: Request, team_id: str):
    """List team members."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    require_team_role(team_id, user_id, "admin")
    return {"members": team_store.list_members(team_id)}


@router.post("/api/teams/{team_id}/invite")
async def invite_member(request: Request, team_id: str, body: InviteRequest):
    """Create an invite link for a team."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    require_team_role(team_id, user_id, "admin")
    if body.role not in ("member", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    invite = team_store.create_invite(team_id, body.email, role=body.role)
    return {
        "success": True,
        "invite": invite,
        "accept_url": f"/app/onboarding?invite={invite['token']}",
    }


@router.post("/api/teams/accept-invite")
async def accept_invite(request: Request, body: AcceptInviteRequest):
    """Accept a team invite."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    team = team_store.accept_invite(body.token, user_id)
    if not team:
        raise HTTPException(status_code=400, detail="Invalid or expired invite")
    return {"success": True, "team": team}


@router.patch("/api/teams/{team_id}/members/{member_user_id}")
async def update_member(request: Request, team_id: str, member_user_id: str, body: MemberRoleUpdate):
    """Update a team member role (owner only)."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    require_team_role(team_id, user_id, "owner")
    if body.role not in ("member", "admin", "owner"):
        raise HTTPException(status_code=400, detail="Invalid role")
    if not team_store.update_member_role(team_id, member_user_id, body.role):
        raise HTTPException(status_code=404, detail="Member not found")
    return {"success": True}


@router.delete("/api/teams/{team_id}/members/{member_user_id}")
async def remove_member(request: Request, team_id: str, member_user_id: str):
    """Remove a team member (owner only)."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    require_team_role(team_id, user_id, "owner")
    if member_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    if not team_store.remove_member(team_id, member_user_id):
        raise HTTPException(status_code=404, detail="Member not found")
    return {"success": True}


@router.post("/api/teams/active")
async def set_active_team(request: Request, body: ActiveTeamRequest):
    """Set active workspace cookie."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    require_team_role(body.team_id, user_id, "member")
    from fastapi.responses import JSONResponse

    resp = JSONResponse({"success": True, "active_team_id": body.team_id})
    secure = __import__("os").environ.get("ENV", "").lower() in ("production", "prod", "staging")
    resp.set_cookie("active_team", body.team_id, httponly=False, secure=secure, samesite="lax", max_age=86400 * 30)
    return resp
