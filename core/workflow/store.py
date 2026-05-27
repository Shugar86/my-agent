"""Workflow persistence layer."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from core import db_manager as _dm


def _db():
    """Return current DBManager singleton (supports test overrides)."""
    return _dm.db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkflowStore:
    """CRUD operations for workflows, runs, and templates."""

    def create_workflow(
        self,
        name: str,
        definition: dict[str, Any],
        owner_id: str | None = None,
        status: str = "draft",
        source_template_id: str | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new workflow."""
        wf_id = f"wf_{uuid.uuid4().hex[:12]}"
        webhook_token = uuid.uuid4().hex
        _db().execute(
            """INSERT INTO workflows
               (id, name, definition_json, status, owner_id, source_template_id, webhook_token, workspace_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (wf_id, name, json.dumps(definition), status, owner_id, source_template_id, webhook_token, workspace_id),
        )
        return self.get_workflow(wf_id)

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        """Fetch workflow by ID."""
        row = _db().fetchone("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
        return self._row_to_workflow(row) if row else None

    def list_workflows(
        self,
        owner_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List workflows, optionally filtered by workspace or owner."""
        if workspace_id:
            rows = _db().fetchall(
                "SELECT * FROM workflows WHERE workspace_id = ? ORDER BY updated_at DESC",
                (workspace_id,),
            )
        elif owner_id:
            rows = _db().fetchall(
                "SELECT * FROM workflows WHERE owner_id = ? ORDER BY updated_at DESC",
                (owner_id,),
            )
        else:
            rows = _db().fetchall("SELECT * FROM workflows ORDER BY updated_at DESC")
        return [self._row_to_workflow(r) for r in rows]

    def user_can_access_workflow(self, workflow_id: str, user_id: str, min_role: str = "member") -> bool:
        """Check if user can access workflow via workspace membership."""
        from core.teams.permissions import has_min_role
        from core.teams.store import team_store

        wf = self.get_workflow(workflow_id)
        if not wf:
            return False
        ws = wf.get("workspace_id")
        if ws:
            role = team_store.get_member_role(ws, user_id)
            return bool(role and has_min_role(role, min_role))
        return wf.get("owner_id") == user_id

    def list_active_workflows(self) -> list[dict[str, Any]]:
        """List all workflows with status=active."""
        rows = _db().fetchall("SELECT * FROM workflows WHERE status = 'active' ORDER BY updated_at DESC")
        return [self._row_to_workflow(r) for r in rows]

    def update_workflow(self, workflow_id: str, **fields: Any) -> dict[str, Any] | None:
        """Update workflow fields."""
        allowed = {"name", "definition_json", "status", "owner_id", "workspace_id"}
        updates = []
        params: list[Any] = []
        for key, val in fields.items():
            if key not in allowed:
                continue
            if key == "definition_json" and isinstance(val, dict):
                val = json.dumps(val)
            updates.append(f"{key} = ?")
            params.append(val)
        if not updates:
            return self.get_workflow(workflow_id)
        updates.append("updated_at = ?")
        params.append(_now_iso())
        params.append(workflow_id)
        _db().execute(f"UPDATE workflows SET {', '.join(updates)} WHERE id = ?", tuple(params))
        return self.get_workflow(workflow_id)

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow by ID."""
        return _db().execute("DELETE FROM workflows WHERE id = ?", (workflow_id,)) > 0

    def create_run(self, workflow_id: str) -> dict[str, Any]:
        """Create a new workflow run record."""
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        _db().execute(
            "INSERT INTO workflow_runs (id, workflow_id, status, log_json) VALUES (?, ?, ?, ?)",
            (run_id, workflow_id, "running", "[]"),
        )
        return {"id": run_id, "workflow_id": workflow_id, "status": "running"}

    def finish_run(self, run_id: str, status: str, logs: list[dict[str, Any]]) -> None:
        """Mark run as completed or failed."""
        _db().execute(
            "UPDATE workflow_runs SET status = ?, finished_at = ?, log_json = ? WHERE id = ?",
            (status, _now_iso(), json.dumps(logs), run_id),
        )

    def update_run_logs(self, run_id: str, logs: list[dict[str, Any]], status: str = "running") -> None:
        """Persist incremental logs during execution."""
        _db().execute(
            "UPDATE workflow_runs SET status = ?, log_json = ? WHERE id = ?",
            (status, json.dumps(logs), run_id),
        )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Fetch a single workflow run."""
        row = _db().fetchone("SELECT * FROM workflow_runs WHERE id = ?", (run_id,))
        return self._row_to_run(row) if row else None

    def list_runs(self, workflow_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """List runs for a workflow."""
        rows = _db().fetchall(
            "SELECT * FROM workflow_runs WHERE workflow_id = ? ORDER BY started_at DESC LIMIT ?",
            (workflow_id, limit),
        )
        return [self._row_to_run(r) for r in rows]

    def list_templates(
        self, category: str | None = None, sort: str = "popular", published_only: bool = True
    ) -> list[dict[str, Any]]:
        """List marketplace workflow templates."""
        order = "installs_count DESC" if sort == "popular" else "created_at DESC"
        where = "WHERE published = 1" if published_only else "WHERE 1=1"
        params: list[Any] = []
        if category:
            where += " AND category = ?"
            params.append(category)
        rows = _db().fetchall(
            f"SELECT * FROM workflow_templates {where} ORDER BY {order}",
            tuple(params),
        )
        templates = [self._row_to_template(r) for r in rows]
        if sort == "popular":
            templates = [
                tpl for tpl in templates
                if "draft" not in (tpl.get("tags") or [])
            ]
        return templates

    def rate_template(self, template_id: str, user_id: str, score: int) -> dict[str, Any] | None:
        """Rate a template 1-5 stars."""
        score = max(1, min(5, score))
        existing = _db().fetchone(
            "SELECT id FROM template_ratings WHERE user_id = ? AND template_id = ?",
            (user_id, template_id),
        )
        if existing:
            _db().execute(
                "UPDATE template_ratings SET score = ? WHERE user_id = ? AND template_id = ?",
                (score, user_id, template_id),
            )
        else:
            _db().execute(
                "INSERT INTO template_ratings (user_id, template_id, score) VALUES (?, ?, ?)",
                (user_id, template_id, score),
            )
        row = _db().fetchone(
            "SELECT AVG(score) as avg, COUNT(*) as cnt FROM template_ratings WHERE template_id = ?",
            (template_id,),
        )
        avg = float(row["avg"] or 0) if row else 0
        cnt = int(row["cnt"] or 0) if row else 0
        _db().execute(
            "UPDATE workflow_templates SET rating_avg = ?, rating_count = ? WHERE id = ?",
            (avg, cnt, template_id),
        )
        return self.get_template(template_id)

    def create_template(
        self,
        name: str,
        description: str,
        category: str,
        definition: dict[str, Any],
        tags: list[str] | None = None,
        author_id: str | None = None,
        published: bool = True,
    ) -> dict[str, Any]:
        """Publish a new workflow template."""
        tpl_id = f"tpl_{uuid.uuid4().hex[:12]}"
        _db().execute(
            """INSERT INTO workflow_templates
               (id, name, description, category, definition_json, tags_json,
                installs_count, author_id, rating_avg, rating_count, published, created_by)
               VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0, 0, ?, ?)""",
            (
                tpl_id, name, description, category,
                json.dumps(definition), json.dumps(tags or []),
                author_id, 1 if published else 0, author_id,
            ),
        )
        return self.get_template(tpl_id)

    def get_template(self, template_id: str) -> dict[str, Any] | None:
        """Fetch template by ID."""
        row = _db().fetchone("SELECT * FROM workflow_templates WHERE id = ?", (template_id,))
        return self._row_to_template(row) if row else None

    def increment_template_installs(self, template_id: str) -> None:
        """Increment install counter for template."""
        _db().execute(
            "UPDATE workflow_templates SET installs_count = installs_count + 1 WHERE id = ?",
            (template_id,),
        )

    def clone_template(
        self, template_id: str, owner_id: str | None, name: str | None = None, workspace_id: str | None = None
    ) -> dict[str, Any] | None:
        """Clone template into a new workflow."""
        template = self.get_template(template_id)
        if not template:
            return None
        wf_name = name or f"{template['name']} (copy)"
        wf = self.create_workflow(
            name=wf_name,
            definition=template["definition"],
            owner_id=owner_id,
            status="draft",
            source_template_id=template_id,
            workspace_id=workspace_id,
        )
        self.increment_template_installs(template_id)
        return wf

    def get_user_profile(self, user_id: str) -> dict[str, Any]:
        """Get or create user profile."""
        row = _db().fetchone("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        if row:
            return {
                "user_id": row["user_id"],
                "onboarding_complete": bool(row["onboarding_complete"]),
                "settings": json.loads(row["settings_json"] or "{}"),
            }
        _db().execute(
            "INSERT INTO user_profiles (user_id, onboarding_complete, settings_json) VALUES (?, ?, ?)",
            (user_id, 0, "{}"),
        )
        return {"user_id": user_id, "onboarding_complete": False, "settings": {}}

    def set_onboarding_complete(self, user_id: str, complete: bool = True) -> None:
        """Mark user onboarding as complete."""
        profile = self.get_user_profile(user_id)
        settings_json = json.dumps(profile.get("settings", {}))
        flag = 1 if complete else 0
        if _db().db_type == "postgres":
            _db().execute(
                """INSERT INTO user_profiles (user_id, onboarding_complete, settings_json)
                   VALUES (?, ?, ?)
                   ON CONFLICT (user_id) DO UPDATE SET
                     onboarding_complete = EXCLUDED.onboarding_complete,
                     settings_json = EXCLUDED.settings_json""",
                (user_id, flag, settings_json),
            )
        else:
            _db().execute(
                """INSERT OR REPLACE INTO user_profiles
                   (user_id, onboarding_complete, settings_json) VALUES (?, ?, ?)""",
                (user_id, flag, settings_json),
            )

    @staticmethod
    def _row_to_workflow(row) -> dict[str, Any]:
        keys = row.keys() if hasattr(row, "keys") else []
        return {
            "id": row["id"],
            "name": row["name"],
            "definition": json.loads(row["definition_json"] or "{}"),
            "status": row["status"],
            "owner_id": row["owner_id"],
            "workspace_id": row["workspace_id"] if "workspace_id" in keys else None,
            "source_template_id": row["source_template_id"],
            "webhook_token": row["webhook_token"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _row_to_run(row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "workflow_id": row["workflow_id"],
            "status": row["status"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "logs": json.loads(row["log_json"] or "[]"),
        }

    @staticmethod
    def _row_to_template(row) -> dict[str, Any]:
        keys = row.keys() if hasattr(row, "keys") else []
        return {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "category": row["category"],
            "definition": json.loads(row["definition_json"] or "{}"),
            "tags": json.loads(row["tags_json"] or "[]"),
            "installs": row["installs_count"],
            "rating_avg": float(row["rating_avg"]) if "rating_avg" in keys and row["rating_avg"] is not None else 0.0,
            "rating_count": int(row["rating_count"]) if "rating_count" in keys and row["rating_count"] is not None else 0,
            "published": bool(row["published"]) if "published" in keys else True,
            "author_id": row["author_id"] if "author_id" in keys else None,
        }


workflow_store = WorkflowStore()
