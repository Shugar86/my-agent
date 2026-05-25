"""Tests for Scheduler skill and SchedulerManager."""
import pytest
from unittest.mock import patch, MagicMock
from core.scheduler_manager import SchedulerManager
from skills.scheduler.skill import schedule_task, cancel_scheduled_task, list_scheduled_tasks


def test_scheduler_manager_start_shutdown():
    mgr = SchedulerManager()
    with patch("core.scheduler_manager.AsyncIOScheduler") as MockSched:
        mock_inst = MagicMock()
        mock_inst.get_jobs.return_value = []
        MockSched.return_value = mock_inst
        import asyncio
        asyncio.run(mgr.start())
        mock_inst.start.assert_called_once()
        asyncio.run(mgr.shutdown())
        mock_inst.shutdown.assert_called_once()


def test_scheduler_manager_add_job():
    mgr = SchedulerManager()
    with patch("core.scheduler_manager.AsyncIOScheduler") as MockSched:
        mock_inst = MagicMock()
        mock_inst.get_jobs.return_value = []
        MockSched.return_value = mock_inst
        import asyncio
        asyncio.run(mgr.start())
        result = asyncio.run(mgr.add_job(
            "task_001", "Check news", "interval", {"minutes": 30}, "news_monitor"
        ))
        assert result["success"] is True
        mock_inst.add_job.assert_called_once()


def test_scheduler_manager_list_jobs():
    mgr = SchedulerManager()
    with patch("core.scheduler_manager.AsyncIOScheduler") as MockSched:
        mock_inst = MagicMock()
        fake_job = MagicMock()
        fake_job.id = "task_001"
        fake_job.next_run_time.isoformat.return_value = "2026-05-24T10:00:00"
        fake_job.trigger = "interval[0:30:00]"
        mock_inst.get_jobs.return_value = [fake_job]
        MockSched.return_value = mock_inst
        import asyncio
        asyncio.run(mgr.start())
        jobs = asyncio.run(mgr.list_jobs())
        assert len(jobs) == 1
        assert jobs[0]["id"] == "task_001"


def test_schedule_task_sync():
    async def _mock_add(*args, **kwargs):
        return {"success": True, "job_id": "task_abc"}

    with patch("skills.scheduler.skill.scheduler_manager") as mock_mgr:
        mock_mgr.add_job = _mock_add
        result = schedule_task("Check news", trigger_type="interval", minutes=30)
        assert result["success"] is True


def test_schedule_task_cron_validation():
    async def _mock_add(*args, **kwargs):
        return {"success": True, "job_id": "task_xyz"}

    with patch("skills.scheduler.skill.scheduler_manager") as mock_mgr:
        mock_mgr.add_job = _mock_add
        result = schedule_task("Daily backup", trigger_type="cron", cron="0 3 * * *")
        assert result["success"] is True


def test_schedule_task_invalid_cron():
    result = schedule_task("Bad cron", trigger_type="cron", cron="invalid")
    assert result["success"] is False
    assert "5 fields" in result["error"]


def test_cancel_scheduled_task():
    async def _mock_remove(*args, **kwargs):
        return {"success": True}

    with patch("skills.scheduler.skill.scheduler_manager") as mock_mgr:
        mock_mgr.remove_job = _mock_remove
        result = cancel_scheduled_task("task_001")
        assert result["success"] is True
