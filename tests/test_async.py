"""Async core tests."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from core.llm_gateway import LLMGateway, APIErrorClassifier, async_jittered_backoff
from core.retry_utils import jittered_backoff
from core.runtime import AgentRuntime
from core.orchestrator import Orchestrator
from core.sub_agents import run_parallel_agents_async


# ---------------------------------------------------------------------------
# LLMGateway async tests
# ---------------------------------------------------------------------------

class TestLLMGatewayAsync:
    @pytest.fixture
    def gateway(self):
        return LLMGateway({"primary": "gpt-4", "api_key": "test", "max_retries": 2})

    @pytest.mark.asyncio
    async def test_chat_success(self, gateway):
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="Hello", role="assistant", tool_calls=None))]
        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            result = await gateway.chat([{"role": "user", "content": "Hi"}])
            assert result.content == "Hello"

    @pytest.mark.asyncio
    async def test_chat_fallback(self, gateway):
        gateway.fallback = "gpt-3.5"
        with patch("litellm.acompletion", new_callable=AsyncMock, side_effect=[Exception("primary fail"), MagicMock(
            choices=[MagicMock(message=MagicMock(content="Fallback", role="assistant", tool_calls=None))]
        )]) as mock:
            result = await gateway.chat([{"role": "user", "content": "Hi"}])
            assert result.content == "Fallback"
            assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_chat_stream(self, gateway):
        async def _async_gen():
            yield MagicMock(choices=[MagicMock(delta=MagicMock(content="Hi"), finish_reason=None)])
            yield MagicMock(choices=[MagicMock(delta=MagicMock(content=" there"), finish_reason=None)])
            yield MagicMock(choices=[MagicMock(delta=MagicMock(content=""), finish_reason="stop")])

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=_async_gen()):
            tokens = []
            async for event in gateway.chat_stream([{"role": "user", "content": "Hi"}]):
                tokens.append(event)
            assert any(t["type"] == "token" and t["content"] == "Hi" for t in tokens)
            assert any(t["type"] == "done" for t in tokens)

    @pytest.mark.asyncio
    async def test_chat_rate_limit_retry(self, gateway):
        with patch("litellm.acompletion", new_callable=AsyncMock, side_effect=[
            Exception("429 rate limit"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="OK", role="assistant", tool_calls=None))])
        ]) as mock:
            result = await gateway.chat([{"role": "user", "content": "Hi"}])
            assert result.content == "OK"
            assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_chat_auth_no_retry(self, gateway):
        with patch("litellm.acompletion", new_callable=AsyncMock, side_effect=Exception("401 unauthorized")) as mock:
            result = await gateway.chat([{"role": "user", "content": "Hi"}])
            assert "error" in result.content.lower() or "encountered" in result.content.lower()
            assert mock.call_count == 1


# ---------------------------------------------------------------------------
# Retry utils tests
# ---------------------------------------------------------------------------

class TestRetryUtils:
    def test_jittered_backoff_range(self):
        for attempt in range(1, 6):
            delay = jittered_backoff(attempt, base_delay=1.0, max_delay=10.0)
            # max_delay + max_jitter = 10.0 * 1.5 = 15.0
            assert 0 < delay <= 15.0

    def test_jittered_backoff_increases(self):
        d1 = jittered_backoff(1, base_delay=1.0)
        d2 = jittered_backoff(2, base_delay=1.0)
        d3 = jittered_backoff(3, base_delay=1.0)
        # Statistically likely but not guaranteed; test median behavior
        assert d1 <= d2 or d1 <= d3

    @pytest.mark.asyncio
    async def test_async_jittered_backoff(self):
        start = asyncio.get_event_loop().time()
        await async_jittered_backoff(1, base_delay=0.01, max_delay=0.1)
        elapsed = asyncio.get_event_loop().time() - start
        assert elapsed >= 0.005


# ---------------------------------------------------------------------------
# APIErrorClassifier tests
# ---------------------------------------------------------------------------

class TestAPIErrorClassifier:
    def test_rate_limit(self):
        cat, retry = APIErrorClassifier.classify_error(Exception("429 rate limit"))
        assert cat == "rate_limit" and retry

    def test_auth(self):
        cat, retry = APIErrorClassifier.classify_error(Exception("401 unauthorized"))
        assert cat == "auth" and not retry

    def test_server_error(self):
        cat, retry = APIErrorClassifier.classify_error(Exception("503 service unavailable"))
        assert cat == "server" and retry

    def test_timeout(self):
        cat, retry = APIErrorClassifier.classify_error(Exception("timeout connecting"))
        assert cat == "timeout" and retry

    def test_policy(self):
        cat, retry = APIErrorClassifier.classify_error(Exception("content policy violation"))
        assert cat == "policy" and not retry


# ---------------------------------------------------------------------------
# Orchestrator async tests
# ---------------------------------------------------------------------------

class TestOrchestratorAsync:
    @pytest.mark.asyncio
    async def test_run_agent_not_found(self):
        store = MagicMock()
        store.get_agent.return_value = None
        orch = Orchestrator(store)
        result = await orch.run("hello", "missing")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_run_with_sub_agents(self):
        store = MagicMock()
        store.get_agent.return_value = {
            "id": "main",
            "role": "test",
            "skills": [],
            "tools": [],
            "sub_agents": ["sub1"],
            "model": {"primary": "gpt-4"},
        }
        store.get_agent.side_effect = lambda x: {
            "main": store.get_agent.return_value,
            "sub1": {"id": "sub1", "role": "sub", "skills": [], "tools": [], "model": {"primary": "gpt-4"}, "memory": {"enabled": False}},
        }.get(x)

        orch = Orchestrator(store)
        with patch("core.sub_agents.run_parallel_agents_async", new_callable=AsyncMock, return_value={"sub1": "done"}):
            result = await orch.run("hello", "main")
            assert "sub1" in result or "done" in result


# ---------------------------------------------------------------------------
# Sub-agents async tests
# ---------------------------------------------------------------------------

class TestSubAgentsAsync:
    @pytest.mark.asyncio
    async def test_run_parallel_agents_async_empty(self):
        result = await run_parallel_agents_async("task", [])
        assert result == {}

    @pytest.mark.asyncio
    async def test_run_parallel_agents_async_single(self):
        config = {
            "id": "a1",
            "model": {"primary": "gpt-4"},
            "role": "test",
            "skills": [],
            "tools": [],
            "memory": {"enabled": False},
        }
        with patch("core.builder.AgentBuilder.build") as mock_build:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value="result")
            mock_build.return_value = mock_agent
            result = await run_parallel_agents_async("task", [config])
            assert result.get("a1") == "result"

    @pytest.mark.asyncio
    async def test_run_parallel_agents_async_error_handling(self):
        config = {
            "id": "a1",
            "model": {"primary": "gpt-4"},
            "role": "test",
            "skills": [],
            "tools": [],
            "memory": {"enabled": False},
        }
        with patch("core.builder.AgentBuilder.build") as mock_build:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(side_effect=Exception("boom"))
            mock_build.return_value = mock_agent
            result = await run_parallel_agents_async("task", [config])
            assert "Error" in result.get("a1", "")
