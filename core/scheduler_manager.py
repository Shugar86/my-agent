"""Task scheduler manager using APScheduler.

Supports cron and interval triggers. Persists jobs to the same database
used by the application (PostgreSQL or SQLite via SQLAlchemyJobStore).
"""
import os
import json
import logging
from typing import Optional
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///data/agent.db")


def _create_jobstores():
    """Create job store dict for scheduler."""
    if DATABASE_URL.startswith("sqlite"):
        # APScheduler requires SQLAlchemy engine; create one for SQLite
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        return {"default": SQLAlchemyJobStore(engine=engine)}
    else:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        return {"default": SQLAlchemyJobStore(engine=engine)}


class SchedulerManager:
    """Manages scheduled agent tasks."""

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None

    async def start(self):
        """Start the async scheduler."""
        if self._scheduler is not None:
            return
        jobstores = _create_jobstores()
        self._scheduler = AsyncIOScheduler(jobstores=jobstores)
        self._scheduler.start()
        logger.info("Scheduler started with %s jobs", len(self._scheduler.get_jobs()))

    async def shutdown(self):
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("Scheduler shutdown")

    async def add_workflow_job(self, job_id: str, workflow_id: str, trigger_args: dict) -> dict:
        """Add a scheduled workflow execution job."""
        if not self._scheduler:
            return {"success": False, "error": "Scheduler not started"}
        try:
            trigger = CronTrigger(**trigger_args)
            self._scheduler.add_job(
                func=_run_workflow_task,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                kwargs={"workflow_id": workflow_id, "job_id": job_id},
            )
            return {"success": True, "job_id": job_id}
        except Exception as e:
            logger.exception("Failed to add workflow job")
            return {"success": False, "error": str(e)}

    async def add_email_poll_job(
        self, job_id: str, workflow_id: str, node_id: str, minutes: int = 5
    ) -> dict:
        """Add an interval job to poll Gmail for workflow email triggers."""
        if not self._scheduler:
            return {"success": False, "error": "Scheduler not started"}
        try:
            trigger = IntervalTrigger(minutes=max(1, minutes))
            self._scheduler.add_job(
                func=_run_email_poll_task,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                kwargs={"workflow_id": workflow_id, "node_id": node_id, "job_id": job_id},
            )
            return {"success": True, "job_id": job_id}
        except Exception as e:
            logger.exception("Failed to add email poll job")
            return {"success": False, "error": str(e)}

    async def add_job(self, job_id: str, description: str, trigger_type: str,
                      trigger_args: dict, agent_role: str = "universal") -> dict:
        """Add a scheduled job.

        trigger_type: 'cron' or 'interval'
        trigger_args: for cron -> dict(month, day, hour, minute, etc.)
                      for interval -> dict(seconds, minutes, hours, days)
        """
        if not self._scheduler:
            return {"success": False, "error": "Scheduler not started"}
        try:
            if trigger_type == "cron":
                trigger = CronTrigger(**trigger_args)
            elif trigger_type == "interval":
                trigger = IntervalTrigger(**trigger_args)
            else:
                return {"success": False, "error": f"Unknown trigger type: {trigger_type}"}

            self._scheduler.add_job(
                func=_run_scheduled_task,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                kwargs={"description": description, "agent_role": agent_role, "job_id": job_id},
            )
            return {"success": True, "job_id": job_id}
        except Exception as e:
            logger.exception("Failed to add job")
            return {"success": False, "error": str(e)}

    async def remove_job(self, job_id: str) -> dict:
        if not self._scheduler:
            return {"success": False, "error": "Scheduler not started"}
        try:
            self._scheduler.remove_job(job_id)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def pause_job(self, job_id: str) -> dict:
        """Pause a scheduled job without deleting it."""
        if not self._scheduler:
            return {"success": False, "error": "Scheduler not started"}
        try:
            self._scheduler.pause_job(job_id)
            return {"success": True, "job_id": job_id, "paused": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def resume_job(self, job_id: str) -> dict:
        """Resume a paused scheduled job."""
        if not self._scheduler:
            return {"success": False, "error": "Scheduler not started"}
        try:
            self._scheduler.resume_job(job_id)
            return {"success": True, "job_id": job_id, "paused": False}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_jobs(self) -> list:
        if not self._scheduler:
            return []
        from core import db_manager as _dm

        jobs = self._scheduler.get_jobs()
        result: list[dict] = []
        log_available = _dm.db.table_exists("scheduled_jobs_log")
        for job in jobs:
            last_row = None
            if log_available:
                last_row = _dm.db.fetchone(
                    """SELECT executed_at, status FROM scheduled_jobs_log
                       WHERE job_id = ? ORDER BY executed_at DESC LIMIT 1""",
                    (job.id,),
                )
            paused = job.next_run_time is None
            result.append(
                {
                    "id": job.id,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "last_run_time": last_row["executed_at"] if last_row else None,
                    "last_run_status": last_row["status"] if last_row else None,
                    "paused": paused,
                    "trigger": str(job.trigger),
                }
            )
        return result

    async def get_job(self, job_id: str) -> Optional[dict]:
        if not self._scheduler:
            return None
        job = self._scheduler.get_job(job_id)
        if not job:
            return None
        return {
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        }


# Singleton
scheduler_manager = SchedulerManager()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_scheduled_job(
    job_id: str,
    description: str,
    result: str,
    status: str,
) -> None:
    """Persist scheduler execution log; skip gracefully if table missing."""
    from core.db_manager import db

    if not db.table_exists("scheduled_jobs_log"):
        logger.warning("scheduled_jobs_log table missing; skipping job log for %s", job_id)
        return
    try:
        db.execute(
            "INSERT INTO scheduled_jobs_log (job_id, description, result, status, executed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (job_id, description, result[:2000], status, _now_iso()),
        )
    except Exception as exc:
        logger.warning("Failed to write scheduled_jobs_log for %s: %s", job_id, exc)


def _run_scheduled_task(description: str, agent_role: str, job_id: str):
    """Callback executed by APScheduler."""
    import asyncio
    logger.info("Scheduled job %s running: %s (role=%s)", job_id, description, agent_role)
    # Fire-and-forget: schedule coroutine on running event loop
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_execute_scheduled(description, agent_role, job_id))
    except RuntimeError:
        # No running loop (e.g., during tests or unusual contexts)
        asyncio.run(_execute_scheduled(description, agent_role, job_id))


async def _execute_scheduled(description: str, agent_role: str, job_id: str):
    """Run the agent for a scheduled task."""
    from core.builder import AgentBuilder
    try:
        builder = AgentBuilder().set_role(agent_role)
        agent = builder.build()
        result = await agent.run(description)
        logger.info("Scheduled job %s completed. Result length: %s", job_id, len(result))
        _log_scheduled_job(job_id, description, result, "success")
    except Exception as e:
        logger.exception("Scheduled job %s failed", job_id)
        _log_scheduled_job(job_id, description, str(e), "error")


def _run_workflow_task(workflow_id: str, job_id: str):
    """Callback for scheduled workflow execution."""
    import asyncio
    logger.info("Scheduled workflow job %s for workflow %s", job_id, workflow_id)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_execute_workflow(workflow_id, job_id))
    except RuntimeError:
        asyncio.run(_execute_workflow(workflow_id, job_id))


async def _execute_workflow(workflow_id: str, job_id: str):
    """Execute a workflow from scheduler."""
    from core.workflow.executor import WorkflowExecutor

    try:
        executor = WorkflowExecutor()
        result = await executor.run(workflow_id, trigger_payload={"scheduled": True, "job_id": job_id})
        status = "success" if result.get("success") else "error"
        _log_scheduled_job(job_id, f"workflow:{workflow_id}", str(result), status)
    except Exception as e:
        logger.exception("Workflow job %s failed", job_id)
        _log_scheduled_job(job_id, f"workflow:{workflow_id}", str(e), "error")


def _run_email_poll_task(workflow_id: str, node_id: str, job_id: str):
    """Callback for email poll jobs."""
    import asyncio
    logger.info("Email poll job %s for workflow %s node %s", job_id, workflow_id, node_id)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_execute_email_poll(workflow_id, node_id, job_id))
    except RuntimeError:
        asyncio.run(_execute_email_poll(workflow_id, node_id, job_id))


async def _execute_email_poll(workflow_id: str, node_id: str, job_id: str):
    """Poll Gmail and trigger workflow on new messages."""
    from core.workflow.executor import WorkflowExecutor
    from core.workflow.store import workflow_store
    from core.workflow.state import load_state, save_state
    try:
        wf = workflow_store.get_workflow(workflow_id)
        if not wf or wf.get("status") != "active":
            return

        owner_id = wf.get("owner_id")
        try:
            from skills.gmail.skill import gmail_list_unread
        except ImportError as exc:
            logger.warning("Gmail skill unavailable for %s: %s", workflow_id, exc)
            return

        result = gmail_list_unread(max_results=10, user_id=owner_id)
        if not result.get("success"):
            logger.warning("Email poll skipped for %s: %s", workflow_id, result.get("error"))
            return

        messages = result.get("messages", [])
        state = load_state(workflow_id)
        seen = set(state.get("last_email_ids", []))
        new_msgs = [m for m in messages if m.get("id") and m["id"] not in seen]
        if not new_msgs:
            return

        all_ids = list(seen | {m["id"] for m in messages if m.get("id")})
        state["last_email_ids"] = all_ids[-50:]
        save_state(workflow_id, state)

        executor = WorkflowExecutor()
        run_result = await executor.run(
            workflow_id,
            trigger_payload={"emails": new_msgs, "email_trigger": True, "node_id": node_id},
            user_id=owner_id,
        )
        status = "success" if run_result.get("success") else "error"
        _log_scheduled_job(job_id, f"email_poll:{workflow_id}", str(run_result), status)
    except Exception as e:
        logger.exception("Email poll job %s failed", job_id)
        _log_scheduled_job(job_id, f"email_poll:{workflow_id}", str(e), "error")
