"""Team workspace persistence."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from core import db_manager as _dm


def _db():
    return _dm.db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "team"
    return f"{base}-{uuid.uuid4().hex[:6]}"


class TeamStore:
    """CRUD for teams, members, and invites."""

    def create_team(self, name: str, owner_id: str, plan: str = "free") -> dict[str, Any]:
        """Create a team and add owner as member."""
        team_id = f"team_{uuid.uuid4().hex[:12]}"
        slug = _slugify(name)
        _db().execute(
            "INSERT INTO teams (id, name, slug, plan, created_at) VALUES (?, ?, ?, ?, ?)",
            (team_id, name, slug, plan, _now_iso()),
        )
        self.add_member(team_id, owner_id, role="owner")
        return self.get_team(team_id) or {}

    def get_team(self, team_id: str) -> dict[str, Any] | None:
        row = _db().fetchone("SELECT * FROM teams WHERE id = ?", (team_id,))
        return self._row_to_team(row) if row else None

    def list_teams_for_user(self, user_id: str) -> list[dict[str, Any]]:
        rows = _db().fetchall(
            """SELECT t.*, tm.role AS member_role
               FROM teams t
               JOIN team_members tm ON tm.team_id = t.id
               WHERE tm.user_id = ?
               ORDER BY t.created_at ASC""",
            (user_id,),
        )
        return [self._row_to_team(r, member_role=r["member_role"]) for r in rows]

    def add_member(self, team_id: str, user_id: str, role: str = "member") -> None:
        if self.get_member_role(team_id, user_id):
            return
        _db().execute(
            "INSERT INTO team_members (team_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
            (team_id, user_id, role, _now_iso()),
        )

    def get_member_role(self, team_id: str, user_id: str) -> str | None:
        row = _db().fetchone(
            "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
            (team_id, user_id),
        )
        return row["role"] if row else None

    def list_members(self, team_id: str) -> list[dict[str, Any]]:
        rows = _db().fetchall(
            "SELECT user_id, role, joined_at FROM team_members WHERE team_id = ? ORDER BY joined_at",
            (team_id,),
        )
        return [{"user_id": r["user_id"], "role": r["role"], "joined_at": r["joined_at"]} for r in rows]

    def update_member_role(self, team_id: str, user_id: str, role: str) -> bool:
        return _db().execute(
            "UPDATE team_members SET role = ? WHERE team_id = ? AND user_id = ?",
            (role, team_id, user_id),
        ) > 0

    def remove_member(self, team_id: str, user_id: str) -> bool:
        return _db().execute(
            "DELETE FROM team_members WHERE team_id = ? AND user_id = ?",
            (team_id, user_id),
        ) > 0

    def create_invite(
        self, team_id: str, email: str, role: str = "member", ttl_hours: int = 72
    ) -> dict[str, Any]:
        token = uuid.uuid4().hex
        expires = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        _db().execute(
            """INSERT INTO team_invites (token, email, team_id, role, expires_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (token, email.lower().strip(), team_id, role, expires.isoformat(), _now_iso()),
        )
        return {"token": token, "email": email, "team_id": team_id, "role": role, "expires_at": expires.isoformat()}

    def get_invite(self, token: str) -> dict[str, Any] | None:
        row = _db().fetchone("SELECT * FROM team_invites WHERE token = ?", (token,))
        if not row:
            return None
        expires = row["expires_at"]
        if isinstance(expires, str):
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        else:
            exp_dt = expires
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        if exp_dt < datetime.now(timezone.utc):
            return None
        return {
            "token": row["token"],
            "email": row["email"],
            "team_id": row["team_id"],
            "role": row["role"],
        }

    def delete_invite(self, token: str) -> None:
        _db().execute("DELETE FROM team_invites WHERE token = ?", (token,))

    def accept_invite(self, token: str, user_id: str) -> dict[str, Any] | None:
        invite = self.get_invite(token)
        if not invite:
            return None
        self.add_member(invite["team_id"], user_id, role=invite["role"])
        self.delete_invite(token)
        return self.get_team(invite["team_id"])

    def ensure_personal_team(self, user_id: str, username: str) -> dict[str, Any]:
        """Ensure user has at least one team; backfill workflow workspace_id."""
        teams = self.list_teams_for_user(user_id)
        if teams:
            team = teams[0]
        else:
            name = f"{username}'s Workspace"
            team = self.create_team(name, user_id)
        self.backfill_workflows(user_id, team["id"])
        return team

    def backfill_workflows(self, user_id: str, team_id: str) -> None:
        """Assign workspace_id to legacy workflows owned by user."""
        _db().execute(
            """UPDATE workflows SET workspace_id = ?
               WHERE owner_id = ? AND (workspace_id IS NULL OR workspace_id = '')""",
            (team_id, user_id),
        )

    def resolve_workspace(self, user_id: str, active_team_id: str | None) -> tuple[str, str]:
        """Return (workspace_id, team_role) for the active or default team."""
        if active_team_id:
            role = self.get_member_role(active_team_id, user_id)
            if role:
                return active_team_id, role
        teams = self.list_teams_for_user(user_id)
        if not teams:
            raise ValueError("User has no team")
        return teams[0]["id"], teams[0].get("member_role", "member")

    @staticmethod
    def _row_to_team(row, member_role: str | None = None) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "plan": row["plan"],
            "created_at": row["created_at"],
            "member_role": member_role,
        }


team_store = TeamStore()
