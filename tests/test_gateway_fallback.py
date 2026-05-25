"""Tests for LLM Gateway overload handling and fallback behavior."""
import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock


class TestOverloadDetection:
    """Tests for APIErrorClassifier overload category."""

    def test_russian_overload_detected(self):
        """Russian 'слишком большая нагрузка' is classified as overload."""
        from core.llm_gateway import APIErrorClassifier

        error = Exception('OpenAIException - Сейчас слишком большая нагрузка, попробуйте позже')
        category, should_retry = APIErrorClassifier.classify_error(error)
        assert category == "overload"
        assert should_retry is True

    def test_english_overload_detected(self):
        """English overload messages are classified correctly."""
        from core.llm_gateway import APIErrorClassifier

        error = Exception("503 Service Unavailable - too much load")
        category, should_retry = APIErrorClassifier.classify_error(error)
        assert category in ["overload", "server"]
        assert should_retry is True

    def test_user_not_found_is_auth(self):
        """User not found error is auth, not overload."""
        from core.llm_gateway import APIErrorClassifier

        error = Exception('{"error":{"message":"User not found.","code":401}}')
        category, should_retry = APIErrorClassifier.classify_error(error)
        assert category == "auth"
        assert should_retry is False

    def test_rate_limit_vs_overload(self):
        """Rate limit and overload are different categories."""
        from core.llm_gateway import APIErrorClassifier

        rate_error = Exception("429 Too Many Requests")
        overload_error = Exception("слишком большая нагрузка")

        rate_cat, _ = APIErrorClassifier.classify_error(rate_error)
        overload_cat, _ = APIErrorClassifier.classify_error(overload_error)

        assert rate_cat == "rate_limit"
        assert overload_cat == "overload"


class TestFallbackMechanism:
    """Tests for LLM Gateway fallback switching."""

    @pytest.fixture
    def dual_config(self):
        """Config with both primary and fallback."""
        return {
            "primary": "openai/gpt-5.4-nano",
            "fallback": "openrouter/owl-alpha",
            "api_key": "test-neuroapi-key",
            "base_url": "https://neuroapi.host/v1",
            "fallback_api_key": "test-openrouter-key",
            "fallback_base_url": "https://openrouter.ai/api/v1",
            "params": {"max_tokens": 50},
            "max_retries": 2,
            "retry_base_delay": 1.0,
            "retry_max_delay": 5.0,
        }

    def test_gateway_has_fallback_attributes(self, dual_config):
        """LLMGateway stores fallback config."""
        from core.llm_gateway import LLMGateway
        gw = LLMGateway(dual_config)
        assert gw.fallback == "openrouter/owl-alpha"
        assert gw.fallback_api_key == "test-openrouter-key"
        assert gw.fallback_base_url == "https://openrouter.ai/api/v1"

    def test_primary_model_configured(self, dual_config):
        """Primary model is correctly set."""
        from core.llm_gateway import LLMGateway
        gw = LLMGateway(dual_config)
        assert gw.primary == "openai/gpt-5.4-nano"
        assert gw.api_key == "test-neuroapi-key"

    def test_build_kwargs_includes_fallback(self, dual_config):
        """_build_kwargs includes fallback settings."""
        from core.llm_gateway import LLMGateway
        gw = LLMGateway(dual_config)
        kwargs = gw._build_kwargs([{"role": "user", "content": "hi"}])
        assert kwargs["model"] == "openai/gpt-5.4-nano"
        assert kwargs["api_key"] == "test-neuroapi-key"

    @pytest.mark.asyncio
    async def test_fallback_switch_on_error(self, dual_config):
        """When primary fails with overload, fallback is attempted."""
        from core.llm_gateway import LLMGateway

        gw = LLMGateway(dual_config)

        # Mock primary to always fail with overload
        with patch('core.llm_gateway.litellm.acompletion', side_effect=[
            Exception("слишком большая нагрузка"),
            Exception("слишком большая нагрузка"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="Fallback response"))])
        ]) as mock_completion:
            result = await gw.chat([{"role": "user", "content": "hi"}])
            # Should have been called 3 times (2 retries on primary + 1 fallback)
            assert mock_completion.call_count >= 2

    def test_error_response_format(self):
        """Error response has expected structure."""
        from core.llm_gateway import LLMGateway
        error = Exception("Test error")
        response = LLMGateway._make_error_response(error)
        assert hasattr(response, 'content')
        assert "error" in response.content.lower()
        assert "error type:" in response.content.lower()

    def test_error_message_truncated(self):
        """Long errors are truncated."""
        from core.llm_gateway import LLMGateway
        long_error = Exception("x" * 1000)
        response = LLMGateway._make_error_response(long_error)
        assert len(response.content) < 1000


class TestConfigAgentJson:
    """Tests for config/agent.json correctness."""

    _CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "agent.json")

    def test_primary_is_neuroapi(self):
        """Primary model is NeuroAPI."""
        import json
        with open(self._CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        assert "neuroapi" in config["model"]["base_url"]
        assert "gpt-5.4-nano" in config["model"]["primary"]

    def test_fallback_is_openrouter(self):
        """Fallback is OpenRouter."""
        import json
        with open(self._CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        assert "openrouter" in config["model"]["fallback_base_url"]
        assert "owl-alpha" in config["model"]["fallback"]

    def test_has_retry_config(self):
        """Config includes retry parameters."""
        import json
        with open(self._CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        assert "max_retries" in config["model"]
        assert "retry_base_delay" in config["model"]
        assert "retry_max_delay" in config["model"]

    def test_env_vars_used(self):
        """API keys use env var syntax."""
        import json
        with open(self._CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        assert "${" in config["model"]["api_key"]
        assert "${" in config["model"]["fallback_api_key"]
