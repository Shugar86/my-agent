#!/usr/bin/env python3
"""Migrate chat sessions from legacy state.db / cli_sessions.db into agent.db.

Idempotent: skips sessions already present in chat_sessions.
Run after `alembic upgrade head`.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _migrate_file(source_path: Path, target_conn: sqlite3.Connection) -> tuple[int, int]:
    """Copy sessions/messages from a legacy StateDB file into agent.db chat tables."""
    if not source_path.exists():
        return 0, 0

    src = sqlite3.connect(str(source_path))
    src.row_factory = sqlite3.Row

    session_table = "chat_sessions" if _table_exists(src, "chat_sessions") else "sessions"
    message_table = "chat_messages" if _table_exists(src, "chat_messages") else "messages"

    if not _table_exists(src, session_table):
        src.close()
        return 0, 0

    sessions = src.execute(f"SELECT * FROM {session_table}").fetchall()
    migrated_sessions = 0
    migrated_messages = 0

    for s in sessions:
        sid = s["id"]
        exists = target_conn.execute(
            "SELECT 1 FROM chat_sessions WHERE id=?", (sid,)
        ).fetchone()
        if exists:
            continue

        cols = s.keys()
        target_conn.execute(
            """INSERT INTO chat_sessions
               (id, source, user_id, model, model_config, system_prompt, parent_session_id,
                started_at, ended_at, end_reason, message_count, tool_call_count, title,
                language, cost_usd, input_tokens, output_tokens, compression_count)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sid,
                s["source"] if "source" in cols else "web",
                s["user_id"] if "user_id" in cols else None,
                s["model"] if "model" in cols else None,
                s["model_config"] if "model_config" in cols else None,
                s["system_prompt"] if "system_prompt" in cols else None,
                s["parent_session_id"] if "parent_session_id" in cols else None,
                s["started_at"],
                s["ended_at"] if "ended_at" in cols else None,
                s["end_reason"] if "end_reason" in cols else None,
                s["message_count"] if "message_count" in cols else 0,
                s["tool_call_count"] if "tool_call_count" in cols else 0,
                s["title"] if "title" in cols else None,
                s["language"] if "language" in cols else None,
                s["cost_usd"] if "cost_usd" in cols else 0,
                s["input_tokens"] if "input_tokens" in cols else 0,
                s["output_tokens"] if "output_tokens" in cols else 0,
                s["compression_count"] if "compression_count" in cols else 0,
            ),
        )
        migrated_sessions += 1

        if _table_exists(src, message_table):
            for m in src.execute(
                f"SELECT * FROM {message_table} WHERE session_id=? ORDER BY timestamp, id",
                (sid,),
            ):
                target_conn.execute(
                    """INSERT INTO chat_messages
                       (session_id, role, content, tool_call_id, tool_calls, tool_name,
                        timestamp, finish_reason)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        sid,
                        m["role"],
                        m["content"],
                        m["tool_call_id"] if "tool_call_id" in m.keys() else None,
                        m["tool_calls"] if "tool_calls" in m.keys() else None,
                        m["tool_name"] if "tool_name" in m.keys() else None,
                        m["timestamp"],
                        m["finish_reason"] if "finish_reason" in m.keys() else None,
                    ),
                )
                migrated_messages += 1

    src.close()
    return migrated_sessions, migrated_messages


def migrate(
    agent_db: Path,
    sources: list[Path],
) -> None:
    """Run migration into agent.db chat tables."""
    if not agent_db.exists():
        print(f"Target DB not found: {agent_db} — run alembic upgrade head first")
        return

    conn = sqlite3.connect(str(agent_db))
    total_s, total_m = 0, 0
    for src in sources:
        s, m = _migrate_file(src, conn)
        print(f"  {src}: {s} sessions, {m} messages")
        total_s += s
        total_m += m
    conn.commit()
    conn.close()
    print(f"Done: {total_s} sessions, {total_m} messages migrated into {agent_db}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy session DBs to agent.db")
    parser.add_argument(
        "--agent-db",
        default="data/agent.db",
        help="Target agent.db path (default: data/agent.db)",
    )
    parser.add_argument(
        "--sources",
        nargs="*",
        default=["data/state.db", "data/cli_sessions.db"],
        help="Legacy session DB files to import",
    )
    args = parser.parse_args()
    migrate(Path(args.agent_db), [Path(p) for p in args.sources])


if __name__ == "__main__":
    main()
