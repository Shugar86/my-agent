"""User Manager — multi‑user support with PostgreSQL and SQLite fallback."""

import os
import json
import uuid
import logging
import re
from datetime import datetime, timezone

import bcrypt

logger = logging.getLogger(__name__)


def _get_db_url():
    return os.environ.get("DATABASE_URL") or None


class UserManager:
    """Manage users, login, registration, and per‑user API keys.

    Uses PostgreSQL (async) when DATABASE_URL is set, otherwise falls back
    to a local SQLite store (sync).
    """

    def __init__(self):
        self._db_url = _get_db_url()
        self._pool = None
        self._sqlite_conn = None
        self._use_pg = bool(
            self._db_url
            and self._db_url.startswith(("postgresql://", "postgres://"))
        )

    async def connect(self):
        if self._use_pg:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                self._db_url, min_size=1, max_size=5, command_timeout=5,
            )
            await self._init_pg()
        else:
            import sqlite3
            from pathlib import Path

            url = self._db_url or "sqlite:///data/agent.db"
            db_path = url.replace("sqlite:///", "", 1)
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self._sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
            self._sqlite_conn.row_factory = sqlite3.Row

    async def close(self):
        if self._pool:
            await self._pool.close()
        if self._sqlite_conn:
            self._sqlite_conn.close()

    # --- Schema ---

    async def _init_pg(self):
        async with self._pool.acquire() as conn:
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS api_keys TEXT DEFAULT '{}'"
            )
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider TEXT DEFAULT 'local'"
            )

    def _password_field(self) -> str:
        return "password_hash"

    @staticmethod
    def _normalize_user(row: dict | None) -> dict | None:
        if not row:
            return None
        user = dict(row)
        if "password_hash" in user and "password" not in user:
            user["password"] = user["password_hash"]
        return user

    def _init_sqlite(self):
        """Schema managed by Alembic — no runtime DDL."""
        pass

    # --- User CRUD ---

    async def create_user(self, username: str, password: str, role: str = "user") -> dict | None:
        existing = await self.get_user_by_username(username)
        if existing:
            return None

        user_id = "u_" + uuid.uuid4().hex[:12]
        pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        now = datetime.now(timezone.utc).timestamp()

        if self._pool:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    f"INSERT INTO users (id, username, {self._password_field()}, role, api_keys, created_at) "
                    "VALUES ($1,$2,$3,$4,$5,NOW())",
                    user_id, username, pwd_hash, role, "{}",
                )
        else:
            self._sqlite_conn.execute(
                "INSERT INTO users (id, username, password_hash, role, api_keys, created_at) VALUES (?,?,?,?,?,?)",
                (user_id, username, pwd_hash, role, "{}", now),
            )
            self._sqlite_conn.commit()

        return {"id": user_id, "username": username, "role": role}

    async def authenticate(self, username: str, password: str) -> dict | None:
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return None
        return user

    async def get_user_by_username(self, username: str) -> dict | None:
        if self._pool:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
                return self._normalize_user(dict(row) if row else None)
        if self._sqlite_conn:
            cur = self._sqlite_conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            return self._normalize_user(dict(row) if row else None)
        return None

    async def get_user_by_id(self, user_id: str) -> dict | None:
        if self._pool:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
                return self._normalize_user(dict(row) if row else None)
        if self._sqlite_conn:
            cur = self._sqlite_conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            return self._normalize_user(dict(row) if row else None)
        return None

    async def update_api_keys(self, user_id: str, keys: dict):
        payload = json.dumps(keys)
        if self._pool:
            async with self._pool.acquire() as conn:
                await conn.execute("UPDATE users SET api_keys = $1 WHERE id = $2", payload, user_id)
        else:
            self._sqlite_conn.execute("UPDATE users SET api_keys = ? WHERE id = ?", (payload, user_id))
            self._sqlite_conn.commit()

    async def get_api_keys(self, user_id: str) -> dict:
        user = await self.get_user_by_id(user_id)
        if user:
            try:
                return json.loads(user.get("api_keys", "{}"))
            except (json.JSONDecodeError, TypeError):
                pass
        return {}

    async def create_default_admin(self):
        """Ensure an admin user exists (for first‑run bootstrap)."""
        admin = await self.get_user_by_username("admin")
        if admin:
            return admin
        return await self.create_user("admin", os.environ.get("AGENT_PASSWORD", "admin"), role="admin")

    async def get_user_by_email(self, email: str) -> dict | None:
        if self._pool:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email.lower())
                return self._normalize_user(dict(row) if row else None)
        if self._sqlite_conn:
            cur = self._sqlite_conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),))
            row = cur.fetchone()
            return dict(row) if row else None
        return None

    async def get_or_create_from_google(self, email: str, name: str | None = None) -> dict | None:
        """Find or create a user from Google OAuth profile."""
        existing = await self.get_user_by_email(email)
        if existing:
            if existing.get("auth_provider") == "local":
                return None
            return existing

        base_username = re.sub(r"[^a-zA-Z0-9_]", "", (email.split("@")[0] or "user"))[:20]
        username = base_username
        suffix = 1
        while await self.get_user_by_username(username):
            username = f"{base_username}{suffix}"
            suffix += 1

        user_id = "u_" + uuid.uuid4().hex[:12]
        pwd_hash = bcrypt.hashpw(uuid.uuid4().hex.encode(), bcrypt.gensalt()).decode()
        now = datetime.now(timezone.utc).timestamp()

        if self._pool:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    f"""INSERT INTO users
                       (id, username, {self._password_field()}, role, api_keys, created_at, email, auth_provider)
                       VALUES ($1,$2,$3,$4,$5,NOW(),$6,$7)""",
                    user_id, username, pwd_hash, "user", "{}", email.lower(), "google",
                )
        else:
            self._sqlite_conn.execute(
                """INSERT INTO users
                   (id, username, password_hash, role, api_keys, created_at, email, auth_provider)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (user_id, username, pwd_hash, "user", "{}", now, email.lower(), "google"),
            )
            self._sqlite_conn.commit()

        return {
            "id": user_id,
            "username": username,
            "role": "user",
            "email": email.lower(),
            "auth_provider": "google",
        }

    async def list_users(self) -> list[dict]:
        if self._pool:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT id, username, role, email, auth_provider, created_at FROM users ORDER BY created_at"
                )
                return [dict(r) for r in rows]
        else:
            cur = self._sqlite_conn.execute(
                "SELECT id, username, role, email, auth_provider, created_at FROM users ORDER BY created_at"
            )
            return [dict(r) for r in cur.fetchall()]
