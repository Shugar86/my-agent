"""Scheduler skill tools."""
from core.tool_registry import registry
from core.scheduler_manager import scheduler_manager


def _run_async(coro):
    """Run an async coroutine from a sync context safely."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Already inside an event loop (e.g., during async tests) — use nest_asyncio approach fallback
    return loop.run_until_complete(coro)


def schedule_task(description: str, trigger_type: str = "interval",
                  minutes: int = 0, hours: int = 0, days: int = 0,
                  cron: str = "", agent_role: str = "universal") -> dict:
    """Schedule a recurring task.

    trigger_type: 'interval' or 'cron'
    For interval: provide minutes/hours/days
    For cron: provide cron expression like '0 9 * * 1' (Monday 9am)
    """
    import uuid
    job_id = f"task_{uuid.uuid4().hex[:8]}"
    if trigger_type == "interval":
        trigger_args = {}
        if minutes:
            trigger_args["minutes"] = minutes
        if hours:
            trigger_args["hours"] = hours
        if days:
            trigger_args["days"] = days
        if not trigger_args:
            return {"success": False, "error": "Interval requires at least minutes, hours, or days"}
    elif trigger_type == "cron":
        if not cron:
            return {"success": False, "error": "Cron trigger requires a cron expression"}
        parts = cron.split()
        if len(parts) != 5:
            return {"success": False, "error": "Cron expression must have 5 fields: min hour day month day_of_week"}
        trigger_args = {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "day_of_week": parts[4],
        }
    else:
        return {"success": False, "error": f"Unknown trigger_type: {trigger_type}"}

    return _run_async(
        scheduler_manager.add_job(job_id, description, trigger_type, trigger_args, agent_role)
    )


def cancel_scheduled_task(job_id: str) -> dict:
    return _run_async(scheduler_manager.remove_job(job_id))


def list_scheduled_tasks() -> dict:
    jobs = _run_async(scheduler_manager.list_jobs())
    return {"success": True, "jobs": jobs}


def get_scheduled_task(job_id: str) -> dict:
    import asyncio
    job = asyncio.get_event_loop().run_until_complete(
        scheduler_manager.get_job(job_id)
    )
    if job:
        return {"success": True, "job": job}
    return {"success": False, "error": "Job not found"}


def register_tools():
    registry.register(
        name="schedule_task",
        description="Schedule a recurring task for the agent (interval or cron).",
        parameters={
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Task description"},
                "trigger_type": {"type": "string", "enum": ["interval", "cron"], "description": "Trigger type"},
                "minutes": {"type": "integer", "description": "Interval minutes"},
                "hours": {"type": "integer", "description": "Interval hours"},
                "days": {"type": "integer", "description": "Interval days"},
                "cron": {"type": "string", "description": "Cron expression (5 fields: min hour day month day_of_week)"},
                "agent_role": {"type": "string", "description": "Agent role to execute task"},
            },
            "required": ["description"],
        },
        execute_fn=schedule_task,
    )
    registry.register(
        name="cancel_scheduled_task",
        description="Cancel a scheduled task by ID.",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job ID to cancel"},
            },
            "required": ["job_id"],
        },
        execute_fn=cancel_scheduled_task,
    )
    registry.register(
        name="list_scheduled_tasks",
        description="List all scheduled tasks.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        execute_fn=list_scheduled_tasks,
    )


def unregister_tools():
    registry.unregister("schedule_task")
    registry.unregister("cancel_scheduled_task")
    registry.unregister("list_scheduled_tasks")
