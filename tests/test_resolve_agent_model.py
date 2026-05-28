"""Tests for resolve_agent_model_config."""

import os

from core.config import resolve_agent_model_config, load_agent_config


def test_resolve_profile_name(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test")
    cfg = resolve_agent_model_config({"model": "balanced"})
    assert cfg["primary"] == "openrouter/owl-alpha"
    assert cfg["api_key"] == "sk-or-v1-test"


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
    defaults = load_agent_config()
    expected = defaults.get("model", {}).get("primary", "")
    assert cfg["primary"] == expected
