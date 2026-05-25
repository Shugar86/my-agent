"""User Manager — multi‑user support with PostgreSQL and SQLite fallback."""

import os
import json
import uuid
import logging
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
        self._use_pg = bool(self._db_url)

    async def connect(self):
        if self._use_pg:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                self._db_url, min_size=1, max_size=5, command_timeout=5,
            )
            await self._init_pg()
        else:
            import sqlite3
            self._sqlite_conn = sqlite3.connect("data/users.db", check_same_thread=False)
            self._sqlite_conn.row_factory = sqlite3.Row
            self._init_sqlite()

    async def close(self):
        if self._pool:
            await self._pool.close()
        if self._sqlite_conn:
            self._sqlite_conn.close()

    # --- Schema ---

    async def _init_pg(self):
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id          TEXT PRIMARY KEY,
                    username    TEXT UNIQUE NOT NULL,
                    password    TEXT NOT NULL,
                    role        TEXT NOT NULL DEFAULT 'user',
                    api_keys    TEXT DEFAULT '{}',
                    created_at  DOUBLE PRECISION NOT NULL
                );
            """)

    def _init_sqlite(self):
        self._sqlite_conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                username    TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                role        TEXT NOT NULL DEFAULT 'user',
                api_keys    TEXT DEFAULT '{}',
                created_at  REAL NOT NULL
            );
        """)
        self._sqlite_conn.commit()

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
                    "INSERT INTO users (id, username, password, role, api_keys, created_at) VALUES ($1,$2,$3,$4,$5,$6)",
                    user_id, username, pwd_hash, role, "{}", now,
                )
        else:
            self._sqlite_conn.execute(
                "INSERT INTO users (id, username, password, role, api_keys, created_at) VALUES (?,?,?,?,?,?)",
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
                return dict(row) if row else None
        else:
            cur = self._sqlite_conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            return dict(row) if row else None

    async def get_user_by_id(self, user_id: str) -> dict | None:
        if self._pool:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
                return dict(row) if row else None
        else:
            cur = self._sqlite_conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None

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

    async def list_users(self) -> list[dict]:
        if self._pool:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("SELECT id, username, role, created_at FROM users ORDER BY created_at")
                return [dict(r) for r in rows]
        else:
            cur = self._sqlite_conn.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at")
            return [dict(r) for r in cur.fetchall()]
