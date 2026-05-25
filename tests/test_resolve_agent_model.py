"""Tests for resolve_agent_model_config."""

import os

from core.config import resolve_agent_model_config


def test_resolve_profile_name(monkeypatch) -> None:
    monkeypatch.setenv("KIMI_API_KEY", "sk-kimi-test")
    cfg = resolve_agent_model_config({"model": "kimi"})
    assert cfg["primary"] == "openai/kimi-for-coding"
    assert cfg["api_key"] == "sk-kimi-test"


def test_resolve_legacy_model_string() -> None:
    cfg = resolve_agent_model_config({
        "model": "openai/custom-model",
        "api_key": "test-key",
        "base_url": "https://example.com/v1",
    })
    assert cfg["primary"] == "openai/custom-model"
    assert cfg["api_key"] == "test-key"


def test_resolve_defaults_from_agent_json() -> None:
    cfg = resolve_agent_model_config({})
    assert cfg["primary"] == "openai/kimi-for-coding"
