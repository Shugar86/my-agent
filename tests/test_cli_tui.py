#!/usr/bin/env python3
"""Tests for CLI TUI (cli/tui.py).

Tests focus on:
- Command parsing (/help, /new, /history, etc.)
- Session management (create, fork, resume, search)
- Rendering (welcome, messages, tables)
- StateDB integration
"""

import pytest
import json
import os
import sys
import time as time_mod
from io import StringIO
from unittest.mock import MagicMock, patch, AsyncMock

# Ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console

from cli.tui import AgentTUI
from core.state_db import StateDB


@pytest.fixture
def mock_agent_config():
    return {
        "id": "test_agent",
        "name": "Test Agent",
        "role": "test role",
        "skills": ["research"],
        "tools": ["web_search"],
        "memory": {"enabled": True},
    }


@pytest.fixture
def mock_store(mock_agent_config):
    store = MagicMock()
    store.get_agent.return_value = mock_agent_config
    store.list_agents.return_value = [mock_agent_config]
    return store


@pytest.fixture
def tui(tmp_path, mock_store):
    """Create a TUI instance with isolated DB."""
    db_path = str(tmp_path / "test_cli.db")
    with patch("cli.tui.AgentStore", return_value=mock_store):
        with patch("cli.tui.load_agent_config", return_value={"model": {}}):
            with patch("cli.tui.resolve_env_vars", side_effect=lambda x: x):
                instance = AgentTUI(
                    agent_id="test_agent",
                    model_profile="fast",
                )
                instance.state_db = StateDB(db_path)
                instance.agent = MagicMock()
                instance.agent.run = MagicMock(return_value="test response")
                yield instance
                instance.state_db.close()


class TestCommands:
    def test_help_command(self, tui, capsys):
        result = tui.handle_command("/help")
        assert result is True
        # Should print table with commands
        captured = capsys.readouterr()
        assert "/help" in captured.out
        assert "/quit" in captured.out

    def test_quit_command(self, tui, capsys):
        result = tui.handle_command("/quit")
        assert result is False
        captured = capsys.readouterr()
        assert "До свидания" in captured.out or "Goodbye" in captured.out

    def test_new_command(self, tui, capsys):
        old_session = tui.session_id
        result = tui.handle_command("/new")
        assert result is True
        assert tui.session_id != old_session
        assert tui.message_count == 0

    def test_clear_command(self, tui, capsys):
        tui.messages = [{"role": "user", "content": "test"}]
        result = tui.handle_command("/clear")
        assert result is True
        assert len(tui.messages) == 0

    def test_model_command_show(self, tui, capsys):
        result = tui.handle_command("/model")
        assert result is True
        captured = capsys.readouterr()
        assert "Profile" in captured.out or "gpt" in captured.out

    def test_model_command_switch(self, tui, capsys):
        with patch("cli.tui.AgentBuilder") as mock_builder:
            mock_builder.return_value.set_model.return_value = mock_builder.return_value
            mock_builder.return_value.set_role.return_value = mock_builder.return_value
            mock_builder.return_value.set_skills.return_value = mock_builder.return_value
            mock_builder.return_value.set_tools.return_value = mock_builder.return_value
            mock_builder.return_value.set_memory.return_value = mock_builder.return_value
            mock_builder.return_value.build.return_value = MagicMock()
            result = tui.handle_command("/model smart")
            assert result is True
            assert tui.model_profile == "smart"

    def test_unknown_command(self, tui, capsys):
        result = tui.handle_command("/unknown")
        assert result is True
        captured = capsys.readouterr()
        assert "Неизвестная" in captured.out or "Unknown" in captured.out


class TestSessionManagement:
    def test_create_session(self, tui):
        tui._create_session()
        session = tui.state_db.get_session(tui.session_id)
        assert session is not None
        assert session["source"] == "cli"

    def test_save_and_load_messages(self, tui):
        tui._create_session()
        tui._save_message("user", "hello")
        tui._save_message("assistant", "hi there")
        messages = tui.state_db.get_messages(tui.session_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    def test_fork_session(self, tui):
        tui._create_session()
        tui._save_message("user", "hello")
        time_mod.sleep(0.01)  # ensure unique IDs
        new_id = tui._fork_session()
        assert new_id != tui.session_id
        messages = tui.state_db.get_messages(new_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "hello"

    def test_set_title(self, tui):
        tui._create_session()
        tui.state_db.set_session_title(tui.session_id, "My Session")
        session = tui.state_db.get_session(tui.session_id)
        assert session["title"] == "My Session"

    def test_search_messages(self, tui):
        tui._create_session()
        tui._save_message("user", "docker compose setup")
        tui._save_message("assistant", "use docker-compose up")
        results = tui.state_db.search_messages("docker")
        assert len(results) >= 1


class TestRendering:
    def test_welcome_screen(self, tui):
        output = StringIO()
        tui.console = Console(file=output, force_terminal=True, width=120)
        tui.render_welcome()
        text = output.getvalue()
        assert "My Agent" in text
        assert "Test Agent" in text

    def test_user_message_render(self, tui):
        output = StringIO()
        tui.console = Console(file=output, force_terminal=True)
        tui.render_user_message("hello world")
        text = output.getvalue()
        assert "hello world" in text

    def test_assistant_message_with_code(self, tui):
        output = StringIO()
        tui.console = Console(file=output, force_terminal=True)
        msg = "```python\nprint('hi')\n```\nSome text"
        tui.render_assistant_message(msg)
        text = output.getvalue()
        assert "print" in text
        assert "Some text" in text

    def test_status_bar(self, tui):
        output = StringIO()
        tui.console = Console(file=output, force_terminal=True)
        tui.render_status_bar()
        text = output.getvalue()
        assert "test_agent" in text


class TestAsyncProcessing:
    @pytest.mark.asyncio
    async def test_process_message(self, tui):
        tui.agent.run = AsyncMock(return_value="response")
        result, latency = await tui.process_message("test")
        assert result == "response"
        assert latency >= 0

    @pytest.mark.asyncio
    async def test_process_message_error(self, tui):
        tui.agent.run = MagicMock(side_effect=Exception("boom"))
        result, latency = await tui.process_message("test")
        assert "Ошибка" in result or "Error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
