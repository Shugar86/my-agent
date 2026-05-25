"""PostgreSQL State Store for My Agent.

Async PostgreSQL implementation that mirrors the SQLite StateDB API.
Used in production deployments; SQLite StateDB remains the default for dev.
"""

import json
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def get_database_url() -> Optional[str]:
    """Return DATABASE_URL from env or None if not configured."""
    return os.environ.get("DATABASE_URL") or None


class PGStateManager:
    """Async PostgreSQL session storage.

    Provides the same API surface as StateDB (SQLite) but uses asyncpg.
    When DATABASE_URL env var is set, MemoryManager auto-selects this backend.
    """

    def __init__(self, dsn: str = None):
        self.dsn = dsn or get_database_url()
        self._pool = None

    async def connect(self):
        if not self.dsn:
            raise ValueError("DATABASE_URL not configured")
        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=1,
                max_size=5,
                command_timeout=5,
            )
            await self._init_schema()
            logger.info("PostgreSQL connected: %s", self.dsn.split("@")[-1] if "@" in self.dsn else "configured")
        except Exception as e:
            logger.error("PostgreSQL connection failed: %s", e)
            raise

    async def _init_schema(self):
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL DEFAULT 'web',
                    user_id TEXT,
                    model TEXT,
                    model_config TEXT,
                    system_prompt TEXT,
                    parent_session_id TEXT,
                    started_at DOUBLE PRECISION NOT NULL,
                    ended_at DOUBLE PRECISION,
                    end_reason TEXT,
                    message_count INTEGER DEFAULT 0,
                    tool_call_count INTEGER DEFAULT 0,
                    title TEXT
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    role TEXT NOT NULL,
                    content TEXT,
                    tool_call_id TEXT,
                    tool_calls TEXT,
                    tool_name TEXT,
                    timestamp DOUBLE PRECISION NOT NULL,
                    finish_reason TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session_pg ON messages(session_id, timestamp);
            """)

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def create_session(self, session_id: str, source: str = "web", **kwargs):
        async with self._pool.acquire() as conn:
            import time
            await conn.execute(
                """INSERT INTO sessions (id, source, user_id, model, model_config, system_prompt,
                   parent_session_id, started_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                   ON CONFLICT (id) DO NOTHING""",
                session_id, source, kwargs.get("user_id"),
                kwargs.get("model"),
                json.dumps(kwargs.get("model_config")) if kwargs.get("model_config") else None,
                kwargs.get("system_prompt"), kwargs.get("parent_session_id"),
                time.time(),
            )

    async def get_session(self, session_id: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM sessions WHERE id = $1", session_id)
            return dict(row) if row else None

    async def add_message(self, session_id: str, role: str, content: str = None, **kwargs):
        async with self._pool.acquire() as conn:
            import time
            await conn.execute(
                """INSERT INTO messages (session_id, role, content, tool_call_id, tool_calls,
                   tool_name, timestamp, finish_reason)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                session_id, role, content, kwargs.get("tool_call_id"),
                json.dumps(kwargs.get("tool_calls")) if kwargs.get("tool_calls") else None,
                kwargs.get("tool_name"), time.time(),
                kwargs.get("finish_reason"),
            )

    async def get_messages(self, session_id: str, limit: int = None) -> list:
        async with self._pool.acquire() as conn:
            if limit:
                rows = await conn.fetch(
                    "SELECT * FROM messages WHERE session_id = $1 ORDER BY timestamp, id LIMIT $2",
                    session_id, limit,
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM messages WHERE session_id = $1 ORDER BY timestamp, id",
                    session_id,
                )
            return [dict(r) for r in rows]

    async def list_sessions(self, limit: int = 30, offset: int = 0) -> list:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, source, started_at, ended_at, message_count, model, title
                   FROM sessions ORDER BY started_at DESC LIMIT $1 OFFSET $2""",
                limit, offset,
            )
            return [dict(r) for r in rows]

    async def delete_session(self, session_id: str):
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM messages WHERE session_id = $1", session_id)
            await conn.execute("DELETE FROM sessions WHERE id = $1", session_id)

    async def search_messages(self, query: str, limit: int = 20) -> list:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT m.session_id, s.title, m.content, m.timestamp
                   FROM messages m JOIN sessions s ON m.session_id = s.id
                   WHERE m.content ILIKE $1
                   ORDER BY m.timestamp DESC LIMIT $2""",
                f"%{query}%", limit,
            )
            return [dict(r) for r in rows]

    async def compress_messages(self, session_id: str, keep_head: int, keep_tail: int, summary_content: str):
        """Replace middle messages with a summary message.
        Deletes and recreates the session to preserve message ordering.
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT role, content, tool_call_id, tool_calls, tool_name FROM messages WHERE session_id = $1 ORDER BY timestamp, id",
                session_id,
            )
            total = len(rows)
            if total <= keep_head + keep_tail + 1:
                return

            await conn.execute("DELETE FROM messages WHERE session_id = $1", session_id)

            import time
            now = time.time()
            idx = 0.0
            # Head
            for r in rows[:keep_head]:
                await conn.execute(
                    """INSERT INTO messages (session_id, role, content, tool_call_id, tool_calls, tool_name, timestamp)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    session_id, r["role"], r["content"], r["tool_call_id"], r["tool_calls"], r["tool_name"], now + idx,
                )
                idx += 1.0

            # Summary
            await conn.execute(
                """INSERT INTO messages (session_id, role, content, timestamp)
                   VALUES ($1, $2, $3, $4)""",
                session_id, "system", f"[CONTEXT SUMMARY]: {summary_content}", now + idx,
            )
            idx += 1.0

            # Tail
            for r in rows[-keep_tail:]:
                await conn.execute(
                    """INSERT INTO messages (session_id, role, content, tool_call_id, tool_calls, tool_name, timestamp)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    session_id, r["role"], r["content"], r["tool_call_id"], r["tool_calls"], r["tool_name"], now + idx,
                )
                idx += 1.0
