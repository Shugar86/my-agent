"""SQLite State Store for My Agent.

Provides persistent session storage with:
- WAL mode for concurrent readers + one writer
- FTS5 full-text search across session messages
- Normalized schema (sessions + messages tables)
- Jittered retry for write-lock contention
- Automatic WAL checkpointing
- Session context compression for long conversations

Inspired by hermes_state.py from Hermes Agent.
"""

import json
import logging
import random
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

SCHEMA_VERSION = 2

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'web',
    user_id TEXT,
    model TEXT,
    model_config TEXT,
    system_prompt TEXT,
    parent_session_id TEXT,
    started_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    title TEXT,
    FOREIGN KEY (parent_session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,
    tool_name TEXT,
    timestamp REAL NOT NULL,
    finish_reason TEXT
);

CREATE TABLE IF NOT EXISTS state_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp);
"""

FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content
);

CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (
        new.id,
        COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
    );
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
    DELETE FROM messages_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
    DELETE FROM messages_fts WHERE rowid = old.id;
    INSERT INTO messages_fts(rowid, content) VALUES (
        new.id,
        COALESCE(new.content, '') || ' ' || COALESCE(new.tool_name, '') || ' ' || COALESCE(new.tool_calls, '')
    );
END;
"""


class StateDB:
    """SQLite-backed session storage with FTS5 search and WAL mode."""

    _WRITE_MAX_RETRIES = 15
    _WRITE_RETRY_MIN_S = 0.020   # 20ms
    _WRITE_RETRY_MAX_S = 0.150   # 150ms
    _CHECKPOINT_EVERY_N_WRITES = 50

    def __init__(self, db_path: str = "data/state.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._write_count = 0

        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=1.0,
            isolation_level=None,
        )
        self._conn.row_factory = sqlite3.Row
        self._setup_wal()
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    def _setup_wal(self):
        """Enable WAL mode with fallback to DELETE on incompatible filesystems."""
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
            logger.debug("WAL mode enabled for %s", self.db_path)
        except sqlite3.OperationalError as exc:
            if "locking protocol" in str(exc).lower():
                logger.warning(
                    "WAL mode unsupported on this filesystem (%s) — "
                    "falling back to DELETE mode (slower but works).",
                    exc,
                )
                self._conn.execute("PRAGMA journal_mode=DELETE")
            else:
                raise

    def _init_schema(self):
        """Create tables, indexes, and FTS5 virtual tables."""
        cursor = self._conn.cursor()
        cursor.executescript(SCHEMA_SQL)

        # FTS5 setup
        try:
            cursor.execute("SELECT * FROM messages_fts LIMIT 0")
        except sqlite3.OperationalError:
            cursor.executescript(FTS_SQL)

        # Schema version bookkeeping
        cursor.execute("SELECT version FROM schema_version LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (SCHEMA_VERSION,),
            )
        elif row[0] < SCHEMA_VERSION:
            cursor.execute(
                "UPDATE schema_version SET version = ?",
                (SCHEMA_VERSION,),
            )
            # Migration: add new columns for CLI v2
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN language TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN cost_usd REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN input_tokens INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN output_tokens INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE sessions ADD COLUMN compression_count INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

        self._conn.commit()

    def _execute_write(self, fn: Callable[[sqlite3.Connection], T]) -> T:
        """Execute a write transaction with BEGIN IMMEDIATE and jitter retry."""
        last_err: Optional[Exception] = None
        for attempt in range(self._WRITE_MAX_RETRIES):
            try:
                with self._lock:
                    self._conn.execute("BEGIN IMMEDIATE")
                    try:
                        result = fn(self._conn)
                        self._conn.commit()
                    except BaseException:
                        try:
                            self._conn.rollback()
                        except Exception:
                            pass
                        raise
                # Success — periodic WAL checkpoint
                self._write_count += 1
                if self._write_count % self._CHECKPOINT_EVERY_N_WRITES == 0:
                    self._try_wal_checkpoint()
                return result
            except sqlite3.OperationalError as exc:
                err_msg = str(exc).lower()
                if "locked" in err_msg or "busy" in err_msg:
                    last_err = exc
                    if attempt < self._WRITE_MAX_RETRIES - 1:
                        jitter = random.uniform(
                            self._WRITE_RETRY_MIN_S,
                            self._WRITE_RETRY_MAX_S,
                        )
                        time.sleep(jitter)
                        continue
                raise
        raise last_err or sqlite3.OperationalError("database is locked after max retries")

    def _try_wal_checkpoint(self) -> None:
        """Best-effort passive WAL checkpoint."""
        try:
            with self._lock:
                result = self._conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
                if result and result[1] > 0:
                    logger.debug("WAL checkpoint: %d/%d pages", result[2], result[1])
        except Exception:
            pass

    def close(self):
        """Close the database connection."""
        with self._lock:
            if self._conn:
                try:
                    self._conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                except Exception:
                    pass
                self._conn.close()
                self._conn = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create_session(
        self,
        session_id: str,
        source: str = "web",
        model: str = None,
        model_config: dict = None,
        system_prompt: str = None,
        user_id: str = None,
        parent_session_id: str = None,
    ) -> str:
        def _do(conn):
            conn.execute(
                """INSERT OR IGNORE INTO sessions
                   (id, source, user_id, model, model_config, system_prompt,
                    parent_session_id, started_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    source,
                    user_id,
                    model,
                    json.dumps(model_config) if model_config else None,
                    system_prompt,
                    parent_session_id,
                    time.time(),
                ),
            )
        self._execute_write(_do)
        return session_id

    def end_session(self, session_id: str, end_reason: str) -> None:
        def _do(conn):
            conn.execute(
                "UPDATE sessions SET ended_at = ?, end_reason = ? WHERE id = ? AND ended_at IS NULL",
                (time.time(), end_reason, session_id),
            )
        self._execute_write(_do)

    def update_message_count(self, session_id: str) -> None:
        def _do(conn):
            count = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,)
            ).fetchone()[0]
            conn.execute(
                "UPDATE sessions SET message_count = ? WHERE id = ?",
                (count, session_id),
            )
        self._execute_write(_do)

    def set_session_title(self, session_id: str, title: str) -> None:
        def _do(conn):
            conn.execute(
                "UPDATE sessions SET title = ? WHERE id = ?",
                (title[:100], session_id),
            )
        self._execute_write(_do)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            cursor = self._conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            )
            row = cursor.fetchone()
        return dict(row) if row else None

    def list_sessions(self, limit: int = 30, offset: int = 0) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """SELECT id, source, started_at, ended_at, message_count,
                          model, title
                   FROM sessions
                   ORDER BY started_at DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_session(self, session_id: str) -> None:
        def _do(conn):
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self._execute_write(_do)

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str = None,
        tool_call_id: str = None,
        tool_calls: str = None,
        tool_name: str = None,
        finish_reason: str = None,
    ) -> int:
        def _do(conn):
            cursor = conn.execute(
                """INSERT INTO messages
                   (session_id, role, content, tool_call_id, tool_calls, tool_name, timestamp, finish_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, tool_call_id, tool_calls, tool_name, time.time(), finish_reason),
            )
            return cursor.lastrowid
        return self._execute_write(_do)

    def get_messages(self, session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        with self._lock:
            sql = "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp, id"
            params = (session_id,)
            if limit:
                sql += " LIMIT ?"
                params = (session_id, limit)
            rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_message_count(self, session_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,)
            ).fetchone()
        return row[0] if row else 0

    def delete_messages(self, session_id: str, keep_last: int = 0) -> None:
        """Delete messages from a session, optionally keeping the last N."""
        def _do(conn):
            if keep_last > 0:
                conn.execute(
                    """DELETE FROM messages WHERE session_id = ? AND id NOT IN (
                        SELECT id FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?
                    )""",
                    (session_id, session_id, keep_last),
                )
            else:
                conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        self._execute_write(_do)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_messages(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Full-text search across all messages using FTS5."""
        with self._lock:
            try:
                rows = self._conn.execute(
                    """SELECT m.session_id, s.title, m.content, m.timestamp
                       FROM messages_fts fts
                       JOIN messages m ON fts.rowid = m.id
                       JOIN sessions s ON m.session_id = s.id
                       WHERE messages_fts MATCH ?
                       ORDER BY rank
                       LIMIT ?""",
                    (query, limit),
                ).fetchall()
                return [dict(r) for r in rows]
            except sqlite3.OperationalError:
                # FTS5 not available or query malformed — fall back to LIKE
                rows = self._conn.execute(
                    """SELECT m.session_id, s.title, m.content, m.timestamp
                       FROM messages m
                       JOIN sessions s ON m.session_id = s.id
                       WHERE m.content LIKE ?
                       ORDER BY m.timestamp DESC
                       LIMIT ?""",
                    (f"%{query}%", limit),
                ).fetchall()
                return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Compression helpers
    # ------------------------------------------------------------------

    def get_message_range(self, session_id: str, start_idx: int, end_idx: int) -> List[Dict[str, Any]]:
        """Get a range of messages by offset (for compression)."""
        with self._lock:
            rows = self._conn.execute(
                """SELECT * FROM messages
                   WHERE session_id = ?
                   ORDER BY timestamp, id
                   LIMIT ? OFFSET ?""",
                (session_id, end_idx - start_idx, start_idx),
            ).fetchall()
        return [dict(r) for r in rows]

    def compress_messages(self, session_id: str, keep_head: int, keep_tail: int, summary_content: str) -> None:
        """Replace middle messages with a summary message."""
        def _do(conn):
            # Count total
            total = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,)
            ).fetchone()[0]

            if total <= keep_head + keep_tail + 1:
                return

            # Delete middle range
            conn.execute(
                """DELETE FROM messages WHERE session_id = ? AND id IN (
                    SELECT id FROM messages WHERE session_id = ?
                    ORDER BY timestamp, id
                    LIMIT ? OFFSET ?
                )""",
                (session_id, session_id, total - keep_head - keep_tail, keep_head),
            )

            # Insert summary
            conn.execute(
                """INSERT INTO messages
                   (session_id, role, content, timestamp)
                   VALUES (?, ?, ?, ?)""",
                (session_id, "system", f"[CONTEXT SUMMARY]: {summary_content}", time.time()),
            )
            # Increment compression counter
            conn.execute(
                "UPDATE sessions SET compression_count = compression_count + 1 WHERE id = ?",
                (session_id,),
            )
        self._execute_write(_do)

    # ------------------------------------------------------------------
    # CLI v2 — cost & token tracking
    # ------------------------------------------------------------------

    def update_session_stats(
        self,
        session_id: str,
        cost_usd: float = None,
        input_tokens: int = None,
        output_tokens: int = None,
        language: str = None,
    ) -> None:
        """Update session stats (cost, tokens, language)."""
        def _do(conn):
            if cost_usd is not None:
                conn.execute(
                    "UPDATE sessions SET cost_usd = cost_usd + ? WHERE id = ?",
                    (cost_usd, session_id),
                )
            if input_tokens is not None:
                conn.execute(
                    "UPDATE sessions SET input_tokens = input_tokens + ? WHERE id = ?",
                    (input_tokens, session_id),
                )
            if output_tokens is not None:
                conn.execute(
                    "UPDATE sessions SET output_tokens = output_tokens + ? WHERE id = ?",
                    (output_tokens, session_id),
                )
            if language is not None:
                conn.execute(
                    "UPDATE sessions SET language = ? WHERE id = ?",
                    (language, session_id),
                )
        self._execute_write(_do)

    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session stats (cost, tokens, compression_count)."""
        with self._lock:
            cursor = self._conn.execute(
                "SELECT cost_usd, input_tokens, output_tokens, compression_count, language FROM sessions WHERE id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
        return dict(row) if row else None
