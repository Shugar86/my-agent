"""Tests for Video Processing skill."""
import os
import pytest
import tempfile


class TestVideoSkill:
    """Tests for skills/video_processing/skill.py."""

    def test_extract_frames_missing_ffmpeg(self):
        """Returns error if ffmpeg not installed."""
        from skills.video_processing.skill import extract_frames
        result = extract_frames("/nonexistent/video.mp4")
        assert "error" in result
        assert "ffmpeg" in result["error"].lower() or "not found" in result["error"].lower()

    def test_get_video_info_missing_file(self):
        """Returns error if video file not found."""
        from skills.video_processing.skill import get_video_info
        result = get_video_info("/nonexistent/video.mp4")
        assert "error" in result

    def test_extract_audio_missing_file(self):
        """Returns error if video file not found."""
        from skills.video_processing.skill import extract_audio
        result = extract_audio("/nonexistent/video.mp4")
        assert "error" in result

    def test_trim_video_missing_file(self):
        """Returns error if video file not found."""
        from skills.video_processing.skill import trim_video
        result = trim_video("/nonexistent/video.mp4", 0, 10)
        assert "error" in result

    def test_register_tools(self):
        """Video tools can be registered."""
        from core.tool_registry import registry
        from skills.video_processing.skill import register_tools, unregister_tools
        register_tools()
        assert registry.has("extract_frames")
        assert registry.has("get_video_info")
        assert registry.has("extract_audio")
        assert registry.has("trim_video")
        unregister_tools()

    def test_unregister_tools(self):
        """Video tools can be unregistered."""
        from core.tool_registry import registry
        from skills.video_processing.skill import register_tools, unregister_tools
        register_tools()
        unregister_tools()
        assert not registry.has("extract_frames")
