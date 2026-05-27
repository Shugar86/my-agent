"""Durable Redis-backed workflow run queue.

Uses RPOPLPUSH (pending → processing) so in-flight jobs survive process restarts.
Falls back to in-process asyncio tasks when Redis is unavailable (dev only).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from core.redis_client import redis_client

logger = logging.getLogger(__name__)

PENDING_KEY = "workflow:runs:pending"
PROCESSING_KEY = "workflow:runs:processing"
_consumer_task: asyncio.Task[None] | None = None


def _encode_job(
    run_id: str,
    workflow_id: str,
    trigger_payload: dict[str, Any] | None,
    user_id: str | None,
) -> str:
    return json.dumps(
        {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "trigger_payload": trigger_payload or {},
            "user_id": user_id,
        },
        separators=(",", ":"),
    )


async def enqueue_run(
    run_id: str,
    workflow_id: str,
    trigger_payload: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> bool:
    """Push a workflow run job onto the durable queue."""
    payload = _encode_job(run_id, workflow_id, trigger_payload, user_id)
    return await redis_client.queue_push(PENDING_KEY, payload)


async def recover_stale_jobs() -> int:
    """Move processing-list jobs back to pending after restart (atomic per job)."""
    if not await redis_client.ping():
        return 0
    recovered = 0
    while True:
        item = await redis_client.queue_rpoplpush(PROCESSING_KEY, PENDING_KEY)
        if not item:
            break
        recovered += 1
    if recovered:
        logger.info("Recovered %d stale workflow jobs from processing queue", recovered)
    return recovered


async def mark_orphaned_runs_failed() -> int:
    """Mark DB runs stuck in 'running' as failed after crash."""
    from core import db_manager as _dm

    rows = _dm.db.fetchall(
        "SELECT id FROM workflow_runs WHERE status = 'running'",
    )
    if not rows:
        return 0
    from core.workflow.store import workflow_store

    for row in rows:
        workflow_store.finish_run(
            row["id"],
            "failed",
            [{"node_id": "", "event": "error", "detail": "Run interrupted by service restart"}],
        )
    logger.warning("Marked %d orphaned workflow runs as failed", len(rows))
    return len(rows)


async def _execute_job(raw: str) -> None:
    from core.workflow.executor import WorkflowExecutor

    data = json.loads(raw)
    executor = WorkflowExecutor()
    run_id = data["run_id"]
    workflow_id = data["workflow_id"]
    try:
        await executor.run(
            workflow_id,
            trigger_payload=data.get("trigger_payload"),
            user_id=data.get("user_id"),
            existing_run_id=run_id,
        )
    except Exception as exc:
        logger.exception("Queued workflow %s run %s failed: %s", workflow_id, run_id, exc)
        from core.workflow.store import workflow_store

        workflow_store.finish_run(
            run_id,
            "failed",
            [{"node_id": "", "event": "error", "detail": str(exc)}],
        )


async def _consumer_loop() -> None:
    """Background worker consuming durable run jobs."""
    while True:
        if not await redis_client.ping():
            await asyncio.sleep(5)
            continue
        raw = await redis_client.queue_pop_durable(PENDING_KEY, PROCESSING_KEY, timeout=5)
        if not raw:
            continue
        try:
            await _execute_job(raw)
        finally:
            await redis_client.queue_remove(PROCESSING_KEY, raw)


async def start_consumer() -> None:
    """Start the background queue consumer (idempotent)."""
    global _consumer_task
    if _consumer_task and not _consumer_task.done():
        return
    await recover_stale_jobs()
    _consumer_task = asyncio.create_task(_consumer_loop())
    logger.info("Workflow run queue consumer started")


async def stop_consumer() -> None:
    """Cancel the background consumer."""
    global _consumer_task
    if _consumer_task and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
    _consumer_task = None


async def run_inline_fallback(
    run_id: str,
    workflow_id: str,
    trigger_payload: dict[str, Any] | None,
    user_id: str | None,
) -> None:
    """Dev fallback when Redis queue is unavailable."""
    raw = _encode_job(run_id, workflow_id, trigger_payload, user_id)
    await _execute_job(raw)
