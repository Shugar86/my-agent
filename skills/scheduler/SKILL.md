---
name: scheduler
description: Schedule recurring or one-time tasks with cron/interval triggers
tools:
  - schedule_task
  - cancel_scheduled_task
  - list_scheduled_tasks
---

# Scheduler Skill

Schedule tasks that run automatically at set intervals or cron times.
Jobs persist across restarts via SQLAlchemyJobStore.
