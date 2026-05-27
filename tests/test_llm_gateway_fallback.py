"""Tests for LLMGateway fallback kwargs."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.llm_gateway import LLMGateway


@pytest.mark.asyncio
async def test_chat_fallback_rebuilds_kwargs():
    """Fallback uses _build_kwargs with fallback model and api_key."""
    gw = LLMGateway(
        {
            "primary": "openai/primary",
            "fallback": "openai/fallback",
            "api_key": "sk-primary-key-123456789012345678",
            "fallback_api_key": "sk-fallback-key-123456789012345678",
            "params": {"temperature": 0.5},
            "max_retries": 1,
        }
    )
    messages = [{"role": "user", "content": "hi"}]

    fake_msg = MagicMock()
    fake_msg.content = "ok"
    fake_msg.tool_calls = None
    fake_choice = MagicMock()
    fake_choice.message = fake_msg
    fake_resp = MagicMock()
    fake_resp.choices = [fake_choice]

    with patch("core.llm_gateway.litellm.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.side_effect = [
            RuntimeError("500 internal server error"),
            fake_resp,
        ]
        await gw.chat(messages)

    assert mock_completion.await_count == 2
    fallback_call_kwargs = mock_completion.await_args_list[1].kwargs
    assert fallback_call_kwargs["model"] == "openai/fallback"
    assert fallback_call_kwargs["api_key"] == "sk-fallback-key-123456789012345678"
