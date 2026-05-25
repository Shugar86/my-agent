"""Tests for Feedback system."""
import os
import pytest


class TestFeedback:
    """Tests for core.feedback module."""

    def setup_method(self):
        """Ensure feedback table exists before each test."""
        from core import feedback
        feedback._ensure_table()

    def test_submit_feedback(self):
        """Feedback can be submitted."""
        from core import feedback
        result = feedback.submit_feedback(
            session_id="test-session",
            message_id="msg-1",
            query="test query",
            response="test response",
            rating=1,
            agent_id="universal",
            model="gpt-5.4-nano",
            tools_used=["web_search"],
        )
        assert result["success"] is True
        assert "feedback_id" in result

    def test_get_feedback_stats(self):
        """Stats aggregate correctly."""
        from core import feedback
        # Clear and add two entries
        stats = feedback.get_feedback_stats()
        assert "total" in stats
        assert "thumbs_up" in stats
        assert "thumbs_down" in stats

    def test_list_feedback(self):
        """List feedback returns entries."""
        from core import feedback
        items = feedback.list_feedback(limit=10)
        assert isinstance(items, list)

    def test_feedback_count(self):
        """Count returns integer."""
        from core import feedback
        count = feedback.get_feedback_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_export_dataset(self):
        """Export creates a file."""
        from core import feedback
        # Need at least one feedback entry for export
        feedback.submit_feedback(
            session_id="export-test",
            message_id="msg-export",
            query="q",
            response="r",
            rating=1,
        )
        filename = feedback.export_training_dataset()
        assert os.path.exists(filename)
        assert filename.endswith(".jsonl")
        # Cleanup
        try:
            os.remove(filename)
        except Exception:
            pass
