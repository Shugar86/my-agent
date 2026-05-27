"""Tests for atomic workflow job recovery."""
from unittest.mock import AsyncMock, patch

import pytest

from core.workflow import run_queue


@pytest.mark.asyncio
async def test_recover_stale_jobs_uses_atomic_rpoplpush():
    """Stale jobs are moved one-by-one without deleting the whole processing list."""
    items = ["job1", "job2", None]
    rpoplpush = AsyncMock(side_effect=items)

    with patch.object(run_queue.redis_client, "ping", new=AsyncMock(return_value=True)), \
         patch.object(run_queue.redis_client, "queue_rpoplpush", new=rpoplpush), \
         patch.object(run_queue.redis_client, "queue_range", new=AsyncMock()) as range_mock, \
         patch.object(run_queue.redis_client, "delete", new=AsyncMock()) as delete_mock:
        count = await run_queue.recover_stale_jobs()

    assert count == 2
    assert rpoplpush.await_count == 3
    range_mock.assert_not_called()
    delete_mock.assert_not_called()
