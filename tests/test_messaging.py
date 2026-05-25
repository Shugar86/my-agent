"""Tests for Messaging skill."""
import pytest
from unittest.mock import patch, MagicMock
from skills.messaging.skill import send_message


def test_send_message_unknown_platform():
    result = send_message("sms", "123", "hello")
    assert result["success"] is False
    assert "Unknown platform" in result["error"]


def test_send_telegram_missing_token():
    result = send_message("telegram", "12345", "hello")
    assert result["success"] is False
    assert "TELEGRAM_BOT_TOKEN" in result["error"]


def test_send_telegram_success():
    with patch("skills.messaging.skill._telegram_send") as mock_send:
        mock_send.return_value = {"success": True, "message_id": 42}
        result = send_message("telegram", "12345", "hello", bot_token="tok")
        assert result["success"] is True
        assert result["message_id"] == 42


def test_send_discord_success():
    with patch("skills.messaging.skill._discord_send") as mock_send:
        mock_send.return_value = {"success": True}
        result = send_message("discord", "https://discord.webhook", "hello")
        assert result["success"] is True


def test_send_slack_success():
    with patch("skills.messaging.skill._slack_send") as mock_send:
        mock_send.return_value = {"success": True, "ts": "123.456"}
        result = send_message("slack", "#general", "hello", slack_token="xoxb")
        assert result["success"] is True


def test_send_email_delegates():
    with patch("skills.messaging.skill.send_email") as mock_email:
        mock_email.return_value = {"success": True}
        result = send_message("email", "to@example.com", "hello", email_config={
            "subject": "Test",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "username": "u",
            "password": "p",
        })
        assert result["success"] is True
        mock_email.assert_called_once()
