"""Memory Manager — dual backend session persistence.

Auto-selects backend:
- SQLite (StateDB) by default for development
- PostgreSQL (PGStateManager) when DATABASE_URL env var is set
"""

import json
import os
import logging
import asyncio
from datetime import datetime

from core.state_db import StateDB
from core.pg_state import PGStateManager, get_database_url

logger = logging.getLogger(__name__)


class MemoryManager:
    def __init__(self, config):
        self.enabled = config.get("enabled", True)
        self.scope = config.get("scope", "task")
        self._use_pg = False
        self._pg = None

        if not self.enabled:
            self._db = None
            return

        pg_url = get_database_url()
        if pg_url:
            self._use_pg = True
            self._pg = PGStateManager(pg_url)
            self._db = None
            logger.info("MemoryManager: PostgreSQL backend")
        else:
            db_path = config.get("path", "data/state.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self._db = StateDB(db_path)
            logger.info("MemoryManager: SQLite backend (%s)", db_path)

    async def connect_pg(self):
        """Initialize PostgreSQL connection pool (call from async startup)."""
        if self._pg:
            await self._pg.connect()

    async def close_pg(self):
        if self._pg:
            await self._pg.close()

    def get_session(self, session_id):
        if not self.enabled:
            return Session(session_id)

        if self._use_pg:
            raise RuntimeError("Use get_session_async for PostgreSQL backend")

        existing = self._db.get_session(session_id)
        if not existing:
            self._db.create_session(session_id, source="agent")
        rows = self._db.get_messages(session_id)
        messages = []
        for row in rows:
            msg = {"role": row["role"], "content": row["content"]}
            if row["tool_call_id"]:
                msg["tool_call_id"] = row["tool_call_id"]
            if row["tool_calls"]:
                msg["tool_calls"] = json.loads(row["tool_calls"])
            messages.append(msg)
        return Session(session_id, messages)

    async def get_session_async(self, session_id):
        if not self.enabled:
            return Session(session_id)
        if not self._pg:
            return self.get_session(session_id)

        existing = await self._pg.get_session(session_id)
        if not existing:
            await self._pg.create_session(session_id, source="agent")
        rows = await self._pg.get_messages(session_id)
        messages = []
        for row in rows:
            msg = {"role": row["role"], "content": row["content"]}
            if row.get("tool_call_id"):
                msg["tool_call_id"] = row["tool_call_id"]
            if row.get("tool_calls"):
                try:
                    msg["tool_calls"] = json.loads(row["tool_calls"])
                except (json.JSONDecodeError, TypeError):
                    pass
            messages.append(msg)
        return Session(session_id, messages)

    def save_session(self, session):
        if not self.enabled:
            return
        if self._use_pg:
            raise RuntimeError("Use save_session_async for PostgreSQL backend")

        for msg in session.messages:
            tool_calls = json.dumps(msg.get("tool_calls")) if msg.get("tool_calls") else None
            self._db.add_message(
                session_id=session.id,
                role=msg.get("role", "user"),
                content=msg.get("content"),
                tool_call_id=msg.get("tool_call_id"),
                tool_calls=tool_calls,
            )

    async def save_session_async(self, session):
        if not self.enabled:
            return
        if not self._pg:
            self.save_session(session)
            return

        for msg in session.messages:
            await self._pg.add_message(
                session_id=session.id,
                role=msg.get("role", "user"),
                content=msg.get("content"),
                tool_call_id=msg.get("tool_call_id"),
                tool_calls=msg.get("tool_calls"),
            )

    def search(self, query):
        if not self.enabled or self._use_pg:
            return []
        return self._db.search_messages(query)

    async def search_async(self, query):
        if not self.enabled or not self._pg:
            return []
        return await self._pg.search_messages(query)

    def list_sessions(self, limit=30, offset=0):
        if not self.enabled or self._use_pg:
            return []
        return self._db.list_sessions(limit, offset)

    async def list_sessions_async(self, limit=30, offset=0):
        if not self.enabled or not self._pg:
            return []
        return await self._pg.list_sessions(limit, offset)

    def delete_session(self, session_id):
        if not self.enabled or self._use_pg:
            return
        self._db.delete_session(session_id)

    async def delete_session_async(self, session_id):
        if not self.enabled or not self._pg:
            return
        await self._pg.delete_session(session_id)

    def get_db(self):
        return self._db

    def compress_session(self, session_id, keep_head=1, keep_tail=1, summary_content="Summarized"):
        """Compress a session by keeping the first `keep_head` messages,
        the last `keep_tail` messages, and inserting a summary message.
        The summary can be provided via `summary_content`; if not, a placeholder is used.
        This implementation works for the SQLite backend used in tests.
        """
        if not self.enabled or self._use_pg:
            return

        # Retrieve current session (creates if missing)
        session = self.get_session(session_id)
        msgs = session.messages

        # Determine slices
        head = msgs[:keep_head] if keep_head > 0 else []
        tail = msgs[-keep_tail:] if keep_tail > 0 else []

        # Build a simple summary message
        summary_msg = {"role": "assistant", "content": summary_content}

        # New message list: head + summary + tail
        new_messages = head + [summary_msg] + tail

        # Replace messages in the SQLite DB
        # Delete existing session data and recreate fresh session entry
        self._db.delete_session(session_id)
        self._db.create_session(session_id, source="agent")
        for msg in new_messages:
            tool_calls = json.dumps(msg.get("tool_calls")) if msg.get("tool_calls") else None
            self._db.add_message(
                session_id=session_id,
                role=msg.get("role", "user"),
                content=msg.get("content"),
                tool_call_id=msg.get("tool_call_id"),
                tool_calls=tool_calls,
            )


    def is_postgres(self):
        return self._use_pg

    async def ensure_session(self, session_id: str) -> "Session":
        """Load or create a session using the active backend."""
        return await self.get_session_async(session_id)

    async def persist_session(self, session: "Session") -> None:
        """Persist session messages using the active backend."""
        await self.save_session_async(session)


class Session:
    def __init__(self, session_id, messages=None):
        self.id = session_id
        self.messages = messages or []
        self.created_at = datetime.now().isoformat()

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content):
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_result(self, tool_call_id, content):
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": str(content),
        })

    def add_tool_call(self, tool_calls):
        self.messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls,
        })
