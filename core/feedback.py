"""Feedback collection and auto-training dataset management.

Stores user thumbs up/down on assistant responses for future fine-tuning.
Uses SQLite via db_manager.
"""
import json
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from core.db_manager import DBManager

logger = logging.getLogger(__name__)

_db: DBManager | None = None


def _get_db() -> DBManager:
    """Lazy DBManager singleton — avoids import-time connection failures."""
    global _db
    if _db is None:
        _db = DBManager()
    return _db


def _ensure_table() -> None:
    """Ensure feedback table exists (Alembic primary, SQLite dev fallback)."""
    db = _get_db()
    if db.table_exists("feedback"):
        return
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            message_id TEXT,
            query TEXT,
            response TEXT,
            rating INTEGER,
            agent_id TEXT,
            model TEXT,
            tools_used TEXT,
            metadata TEXT,
            created_at TEXT
        )
        """
    )


def submit_feedback(
    session_id: str,
    message_id: str,
    query: str,
    response: str,
    rating: int,  # 1 or -1
    agent_id: str = "universal",
    model: str = "",
    tools_used: List[str] = None,
    metadata: Dict = None,
) -> Dict:
    """Submit user feedback on a response."""
    try:
        _ensure_table()
    except (RuntimeError, OSError) as exc:
        logger.error("Feedback DB unavailable: %s", exc)
        return {"success": False, "error": "Feedback storage unavailable"}

    feedback_id = f"fb-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    try:
        _get_db().execute(
            """
            INSERT INTO feedback (id, session_id, message_id, query, response, rating, agent_id, model, tools_used, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback_id,
                session_id,
                message_id,
                query,
                response,
                rating,
                agent_id,
                model,
                json.dumps(tools_used or [], ensure_ascii=False),
                json.dumps(metadata or {}, ensure_ascii=False),
                now,
            ),
        )
    except (RuntimeError, OSError) as exc:
        logger.error("Failed to save feedback: %s", exc)
        return {"success": False, "error": str(exc)}

    return {"success": True, "feedback_id": feedback_id}


def get_feedback_stats(session_id: str = None, agent_id: str = None) -> Dict:
    """Get aggregated feedback statistics."""
    _ensure_table()
    db = _get_db()
    where = []
    params = []
    if session_id:
        where.append("session_id = ?")
        params.append(session_id)
    if agent_id:
        where.append("agent_id = ?")
        params.append(agent_id)

    if where:
        where_clause = "WHERE " + " AND ".join(where)
    else:
        where_clause = ""

    total_sql = f"SELECT COUNT(*) as count FROM feedback {where_clause}"
    total = db.fetchone(total_sql, tuple(params))

    up_params = params + [1]
    up_where = (where + ["rating = ?"]) if where else ["rating = ?"]
    up_clause = "WHERE " + " AND ".join(up_where)
    thumbs_up = db.fetchone(f"SELECT COUNT(*) as count FROM feedback {up_clause}", tuple(up_params))

    down_params = params + [-1]
    down_where = (where + ["rating = ?"]) if where else ["rating = ?"]
    down_clause = "WHERE " + " AND ".join(down_where)
    thumbs_down = db.fetchone(f"SELECT COUNT(*) as count FROM feedback {down_clause}", tuple(down_params))

    return {
        "total": total["count"] if total else 0,
        "thumbs_up": thumbs_up["count"] if thumbs_up else 0,
        "thumbs_down": thumbs_down["count"] if thumbs_down else 0,
        "score": (thumbs_up["count"] - thumbs_down["count"]) if total and total["count"] > 0 else 0,
    }


def list_feedback(limit: int = 100, offset: int = 0, rating: int = None) -> List[Dict]:
    """List feedback entries."""
    _ensure_table()
    db = _get_db()
    where = []
    params = []
    if rating is not None:
        where.append("rating = ?")
        params.append(rating)

    where_clause = "WHERE " + " AND ".join(where) if where else ""
    sql = f"SELECT * FROM feedback {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = db.fetchall(sql, tuple(params))
    result = []
    for row in rows:
        d = dict(row)
        try:
            d["tools_used"] = json.loads(d.get("tools_used", "[]"))
        except json.JSONDecodeError:
            d["tools_used"] = []
        try:
            d["metadata"] = json.loads(d.get("metadata", "{}"))
        except json.JSONDecodeError:
            d["metadata"] = {}
        result.append(d)
    return result


def export_training_dataset(format: str = "jsonl") -> str:
    """Export feedback as training dataset for fine-tuning.

    Returns path to exported file.
    """
    _ensure_table()
    rows = _get_db().fetchall(
        "SELECT query, response, rating FROM feedback WHERE rating != 0 ORDER BY created_at DESC"
    )

    lines = []
    for row in rows:
        query = row["query"]
        response = row["response"]
        rating = row["rating"]
        if format == "jsonl":
            if rating == 1:
                lines.append(json.dumps({
                    "messages": [
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": response},
                    ]
                }, ensure_ascii=False))
            elif rating == -1:
                lines.append(json.dumps({
                    "prompt": query,
                    "rejected": response,
                }, ensure_ascii=False))

    output_dir = "data/feedback"
    import os
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/training_dataset_{int(time.time())}.jsonl"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return filename


def get_feedback_count() -> int:
    """Get total number of feedback entries."""
    _ensure_table()
    row = _get_db().fetchone("SELECT COUNT(*) as count FROM feedback")
    return row["count"] if row else 0
