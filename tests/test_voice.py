"""Tests for Voice I/O skill."""
import pytest


class TestVoiceSkill:
    """Tests for skills/voice_io/skill.py."""

    def test_transcribe_audio_no_api_key(self):
        """Returns error if OPENAI_API_KEY not set."""
        import os
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            from skills.voice_io.skill import transcribe_audio
            result = transcribe_audio("/nonexistent/audio.mp3")
            assert "error" in result
            assert "OPENAI_API_KEY" in result["error"]
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    def test_transcribe_audio_missing_file(self):
        """Returns error if file not found."""
        import os
        os.environ["OPENAI_API_KEY"] = "test-key"
        try:
            from skills.voice_io.skill import transcribe_audio
            result = transcribe_audio("/nonexistent/audio.mp3")
            assert "error" in result
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_speak_text_no_edge_tts(self):
        """Returns error if edge_tts not installed."""
        import sys
        # Temporarily remove edge_tts from modules
        old = sys.modules.pop("edge_tts", None)
        try:
            import asyncio
            from skills.voice_io.skill import speak_text
            result = asyncio.get_event_loop().run_until_complete(
                speak_text("Hello world")
            )
            assert "error" in result
            assert "edge_tts" in result["error"]
        finally:
            if old:
                sys.modules["edge_tts"] = old

    def test_list_voices_structure(self):
        """List voices returns dict with error if edge_tts missing."""
        from skills.voice_io.skill import list_voices
        result = list_voices("en")
        assert isinstance(result, dict)
        assert "error" in result or "voices" in result

    def test_register_tools(self):
        """Voice tools can be registered."""
        from core.tool_registry import registry
        from skills.voice_io.skill import register_tools, unregister_tools
        register_tools()
        assert registry.has("transcribe_audio")
        assert registry.has("speak_text")
        assert registry.has("list_tts_voices")
        unregister_tools()

    def test_unregister_tools(self):
        """Voice tools can be unregistered."""
        from core.tool_registry import registry
        from skills.voice_io.skill import register_tools, unregister_tools
        register_tools()
        unregister_tools()
        assert not registry.has("transcribe_audio")
