"""Team role-based access control helpers."""

from __future__ import annotations

from fastapi import HTTPException

from core.teams.store import team_store

ROLE_RANK = {"member": 1, "admin": 2, "owner": 3}


def has_min_role(actual: str, required: str) -> bool:
    """Return True if actual role meets or exceeds required role."""
    return ROLE_RANK.get(actual, 0) >= ROLE_RANK.get(required, 0)


def require_team_role(team_id: str, user_id: str, min_role: str = "member") -> str:
    """Verify user membership and return their team role.

    Raises:
        HTTPException: If user lacks required role.
    """
    role = team_store.get_member_role(team_id, user_id)
    if not role:
        raise HTTPException(status_code=403, detail="Not a team member")
    if not has_min_role(role, min_role):
        raise HTTPException(status_code=403, detail="Insufficient team permissions")
    return role
