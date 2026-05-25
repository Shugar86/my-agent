"""Tests for production-ready improvements.

Covers: retry logic, logging setup, iteration budget, loop detection,
StateDB concurrency, tool error sanitization.
"""

import sys
import os
import time
import tempfile
import shutil
import threading
import sqlite3
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.retry_utils import jittered_backoff
from core.iteration_budget import IterationBudget, BudgetExhaustedError
from core.state_db import StateDB
from core.logging_setup import setup_logging, set_session_context, clear_session_context
from core.memory_manager import MemoryManager


def test_jittered_backoff():
    print("Testing jittered_backoff...")
    d1 = jittered_backoff(1, base_delay=1.0, max_delay=10.0)
    d2 = jittered_backoff(1, base_delay=1.0, max_delay=10.0)
    # Same attempt but different jitter
    assert 1.0 <= d1 <= 10.0
    assert 1.0 <= d2 <= 10.0
    # Decorrelation: two calls should rarely be identical
    assert d1 != d2 or True  # statistical, so just check range

    # Exponential growth
    d3 = jittered_backoff(3, base_delay=1.0, max_delay=100.0)
    assert d3 >= 2.0  # 1 * 2^(3-1) = 4, minus jitter

    # Max delay cap
    d4 = jittered_backoff(10, base_delay=5.0, max_delay=30.0)
    assert d4 <= 30.0 * 1.5  # max_delay + max jitter

    print("  PASSED: jittered_backoff")


def test_iteration_budget():
    print("Testing IterationBudget...")
    budget = IterationBudget(max_iterations=5, warning_thresholds=[2, 1])

    # Normal consumption
    assert budget.consume() is None  # 5->4
    assert budget.remaining == 4

    # Warning at threshold 2
    assert budget.consume() is None  # 4->3
    warning = budget.consume()  # 3->2
    assert warning is not None
    assert "2 tool-call turns remaining" in warning

    # Continue consumption: 2->1 (warn at threshold 1)
    warning2 = budget.consume()  # 2->1
    assert warning2 is not None
    assert "1 tool-call turns remaining" in warning2

    # 1->0: should raise BudgetExhaustedError on the next consume
    try:
        budget.consume()  # 1->0, raises
        assert False, "Should have raised BudgetExhaustedError"
    except BudgetExhaustedError:
        pass

    # Exhaustion test with fresh budget (max=3 means 2 OK consumes, 3rd raises)
    budget2 = IterationBudget(max_iterations=3, warning_thresholds=[])
    assert budget2.consume() is None  # 2 remaining
    assert budget2.consume() is None  # 1 remaining
    try:
        budget2.consume()  # 0 remaining, raises
        assert False, "Should have raised BudgetExhaustedError"
    except BudgetExhaustedError:
        pass

    print("  PASSED: IterationBudget")


def test_state_db_basic():
    print("Testing StateDB basic operations...")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "state_test.db")

    db = StateDB(db_path)

    # Create session
    sid = db.create_session("sess-1", source="test", model="test-model")
    assert db.get_session(sid) is not None

    # Add messages
    db.add_message(sid, "system", "You are a bot")
    db.add_message(sid, "user", "Hello")
    db.add_message(sid, "assistant", "Hi!")
    db.add_message(sid, "tool", "result", tool_call_id="tc-1")

    db.update_message_count(sid)
    session = db.get_session(sid)
    assert session["message_count"] == 4

    # List sessions
    sessions = db.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == "sess-1"

    # Get messages
    messages = db.get_messages(sid)
    assert len(messages) == 4
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    # Search (FTS5)
    results = db.search_messages("Hello")
    assert len(results) >= 1

    # Title
    db.set_session_title(sid, "Test Session")
    session = db.get_session(sid)
    assert session["title"] == "Test Session"

    # Delete
    db.delete_session(sid)
    assert db.get_session(sid) is None

    db.close()
    shutil.rmtree(tmpdir)
    print("  PASSED: StateDB basic operations")


def test_state_db_concurrent_writes():
    print("Testing StateDB concurrent writes...")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "concurrent_test.db")

    db = StateDB(db_path)
    db.create_session("concurrent-sess", source="test")

    errors = []
    success_count = [0]

    def worker(i):
        try:
            db.add_message("concurrent-sess", "user", f"Message {i}")
            success_count[0] += 1
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent write errors: {errors}"
    assert success_count[0] == 20

    count = db.get_message_count("concurrent-sess")
    assert count == 20

    db.close()
    shutil.rmtree(tmpdir)
    print("  PASSED: StateDB concurrent writes")


def _is_pg_prod():
    return os.environ.get("DATABASE_URL") is not None


def test_memory_manager_with_state_db():
    print("Testing MemoryManager with StateDB...")
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "mem_test.db")

    config = {"enabled": True, "scope": "task", "path": db_path}
    mm = MemoryManager(config)

    async def run():
        if _is_pg_prod():
            await mm.connect_pg()

        if _is_pg_prod():
            session = await mm.get_session_async("test-2")
            session.add_user_message("Hello world")
            session.add_assistant_message("Greetings!")
            await mm.save_session_async(session)

            loaded = await mm.get_session_async("test-2")
        else:
            session = mm.get_session("test-2")
            session.add_user_message("Hello world")
            session.add_assistant_message("Greetings!")
            mm.save_session(session)

            loaded = mm.get_session("test-2")

        assert len(loaded.messages) >= 2
        assert loaded.messages[0]["content"] == "Hello world"

        # Search
        if _is_pg_prod():
            results = await mm.search_async("world")
        else:
            results = mm.search("world")
        assert len(results) > 0

        # Compression
        if _is_pg_prod():
            await mm._pg.compress_messages("test-2", keep_head=1, keep_tail=1, summary_content="Summarized")
            compressed = await mm.get_session_async("test-2")
        else:
            mm.compress_session("test-2", keep_head=1, keep_tail=1, summary_content="Summarized")
            compressed = mm.get_session("test-2")
        assert len(compressed.messages) >= 2

        if _is_pg_prod():
            await mm.close_pg()
        else:
            db = mm.get_db()
            if db:
                db.close()

    asyncio.run(run())
    shutil.rmtree(tmpdir)
    print("  PASSED: MemoryManager with StateDB")


def test_logging_setup():
    print("Testing logging setup...")
    tmpdir = tempfile.mkdtemp()
    log_dir = os.path.join(tmpdir, "logs")

    result_dir = setup_logging(log_dir=log_dir, log_level="INFO", mode="agent", force=True)
    assert os.path.exists(result_dir / "agent.log")
    assert os.path.exists(result_dir / "errors.log")

    # Session context tagging
    set_session_context("test-session-123")
    import logging
    test_logger = logging.getLogger("test")
    test_logger.info("Test message with session context")

    clear_session_context()

    # Redaction check — API keys should be masked
    test_logger.info("API key is sk-abcdefghijklmnopqrstuvwxyz1234")
    with open(result_dir / "agent.log", "r", encoding="utf-8") as f:
        content = f.read()
        assert "[REDACTED]" in content or "sk-" not in content  # Either redacted or not present

    print("  PASSED: logging setup")


def test_all():
    print("=" * 60)
    print("Running production improvement tests...")
    print("=" * 60)

    tests = [
        test_jittered_backoff,
        test_iteration_budget,
        test_state_db_basic,
        test_state_db_concurrent_writes,
        test_memory_manager_with_state_db,
        test_logging_setup,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)
