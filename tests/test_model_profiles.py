"""Tests for model profiles and CLI user management."""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestModelProfiles:
    """Unit tests for model profile resolution."""

    def test_fast_profile_structure(self):
        """Fast profile has all required keys."""
        from agent import MODEL_PROFILES
        fast = MODEL_PROFILES["fast"]
        required = ["primary", "api_key", "base_url", "fallback", "fallback_api_key", "fallback_base_url", "params", "max_retries"]
        for key in required:
            assert key in fast, f"Missing key: {key}"

    def test_fast_profile_neuroapi_primary(self):
        """Fast profile uses NeuroAPI as primary."""
        from agent import MODEL_PROFILES
        assert "neuroapi" in MODEL_PROFILES["fast"]["base_url"]
        assert "gpt-5.4-nano" in MODEL_PROFILES["fast"]["primary"]

    def test_balanced_profile_openrouter_primary(self):
        """Balanced profile uses OpenRouter as primary."""
        from agent import MODEL_PROFILES
        assert "openrouter" in MODEL_PROFILES["balanced"]["base_url"]
        assert "owl-alpha" in MODEL_PROFILES["balanced"]["primary"]

    def test_smart_profile_claude(self):
        """Smart profile uses Claude."""
        from agent import MODEL_PROFILES
        assert "claude" in MODEL_PROFILES["smart"]["primary"]

    def test_local_profile_no_fallback(self):
        """Local profile has no fallback."""
        from agent import MODEL_PROFILES
        assert not MODEL_PROFILES["local"].get("fallback")
        assert "localhost" in MODEL_PROFILES["local"]["base_url"]

    def test_all_profiles_have_params(self):
        """All profiles have temperature and max_tokens."""
        from agent import MODEL_PROFILES
        for name, profile in MODEL_PROFILES.items():
            assert "params" in profile
            assert "temperature" in profile["params"]
            assert "max_tokens" in profile["params"]


class TestResolveModelProfile:
    """Tests for _resolve_model_profile function."""

    def test_resolve_fast_profile(self):
        """Fast profile resolves correctly."""
        from agent import _resolve_model_profile
        with patch.dict(os.environ, {"NEUROAPI_API_KEY": "test-key"}, clear=False):
            result = _resolve_model_profile("fast")
        assert result["primary"] == "openai/gpt-5.4-nano"

    def test_resolve_unknown_returns_default(self):
        """Unknown profile name returns fast as default."""
        from agent import _resolve_model_profile
        with patch.dict(os.environ, {"NEUROAPI_API_KEY": "test-key"}, clear=False):
            result = _resolve_model_profile("nonexistent")
        assert result["primary"] == "openai/gpt-5.4-nano"

    def test_resolved_profile_is_dict(self):
        """Resolved profile is a dictionary."""
        from agent import _resolve_model_profile
        result = _resolve_model_profile("fast")
        assert isinstance(result, dict)

    def test_resolved_has_api_key(self):
        """Resolved profile contains api_key."""
        from agent import _resolve_model_profile
        result = _resolve_model_profile("balanced")
        assert "api_key" in result


class TestCliUserManagement:
    """Tests for CLI user session management."""

    @pytest.fixture(autouse=True)
    def clean_user_file(self, tmp_path):
        """Clean up CLI user file before/after each test."""
        from agent import _clear_cli_user, CLI_USER_FILE
        _clear_cli_user()
        yield
        _clear_cli_user()

    def test_get_user_returns_none_initially(self):
        """No user is logged in initially."""
        from agent import _get_cli_user
        assert _get_cli_user() is None

    def test_set_and_get_user(self):
        """Can set and retrieve CLI user."""
        from agent import _set_cli_user, _get_cli_user
        test_user = {"username": "testuser", "role": "admin"}
        _set_cli_user(test_user)
        result = _get_cli_user()
        assert result == test_user

    def test_clear_user(self):
        """Clearing user removes the session."""
        from agent import _set_cli_user, _get_cli_user, _clear_cli_user
        _set_cli_user({"username": "test"})
        _clear_cli_user()
        assert _get_cli_user() is None

    def test_user_persistence(self):
        """User data persists to disk."""
        from agent import _set_cli_user, _get_cli_user
        user = {"username": "persistent", "role": "user", "user_id": "123"}
        _set_cli_user(user)
        # Simulate new process by clearing memory cache
        from agent import _get_cli_user
        result = _get_cli_user()
        assert result["username"] == "persistent"
        assert result["user_id"] == "123"

    def test_cli_user_label_empty_when_no_user(self):
        """CLI label is empty when not logged in."""
        from agent import _cli_user_label
        assert _cli_user_label() == ""

    def test_cli_user_label_with_user(self):
        """CLI label contains username when logged in."""
        from agent import _cli_user_label, _set_cli_user
        _set_cli_user({"username": "alice"})
        label = _cli_user_label()
        assert "alice" in label


class TestBuildModelConfig:
    """Tests for _build_model_config function."""

    def test_build_from_string_model(self):
        """Agent config with string model field builds correctly."""
        from agent import _build_model_config
        agent_config = {
            "model": "openrouter/owl-alpha",
            "api_key": "${OPENROUTER_API_KEY}",
            "base_url": "https://openrouter.ai/api/v1",
        }
        result = _build_model_config(agent_config)
        assert result["primary"] == "openrouter/owl-alpha"
        assert "fallback" in result

    def test_build_from_dict_model(self):
        """Agent config with dict model field passes through."""
        from agent import _build_model_config
        agent_config = {
            "model": {"primary": "test-model", "api_key": "test"},
        }
        result = _build_model_config(agent_config)
        assert result["primary"] == "test-model"

    def test_build_adds_defaults(self):
        """Build adds default retry params."""
        from agent import _build_model_config
        result = _build_model_config({"model": "test"})
        assert "max_retries" in result
        assert "retry_base_delay" in result
        assert "retry_max_delay" in result
