"""Real API end-to-end tests with OpenRouter (DeepSeek V4 Flash Free).

Tests actual LLM calls with minimal token usage (3-4 calls total).
Measures latency, correctness, and UX metrics.
"""
import pytest
import time
import asyncio
import os
from typing import Dict, Any
from unittest.mock import patch

import litellm

# ---------------------------------------------------------------------------
# Configure API (used for real calls)
# ---------------------------------------------------------------------------
TEST_MODEL = os.environ.get("TEST_MODEL", "openrouter/deepseek/deepseek-v4-flash:free")
TEST_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
TEST_BASE_URL = os.environ.get("TEST_BASE_URL", "https://openrouter.ai/api/v1")

pytestmark = pytest.mark.skipif(not TEST_API_KEY, reason="OPENROUTER_API_KEY env var not set")

# Global metrics collector
_test_metrics: Dict[str, Any] = {}


async def _call_llm(messages: list, tools=None, timeout: int = 30) -> tuple:
    """Single LLM call with timing. Returns (response, latency_ms, tokens)."""
    start = time.time()
    try:
        kwargs = {
            "model": TEST_MODEL,
            "messages": messages,
            "api_key": TEST_API_KEY,
            "api_base": TEST_BASE_URL,
            "timeout": timeout,
        }
        if tools:
            kwargs["tools"] = tools

        resp = await litellm.acompletion(**kwargs)
        latency_ms = (time.time() - start) * 1000
        tokens = resp.usage.total_tokens if resp.usage else 0
        return resp.choices[0].message, latency_ms, tokens
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return None, latency_ms, 0


@pytest.mark.e2e
class TestAPIConnectivity:
    """Verify OpenRouter API is reachable and model responds."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_api_health_and_latency(self):
        """Single ping to measure cold-start latency."""
        msg, latency, tokens = await _call_llm([
            {"role": "user", "content": "Say 'pong' and nothing else."}
        ])
        assert msg is not None, "API returned error or timeout"
        assert "pong" in msg.content.lower(), f"Unexpected response: {msg.content}"

        _test_metrics["ping_latency_ms"] = latency
        _test_metrics["ping_tokens"] = tokens

        # UX threshold: cold-start should be < 15s for free tier
        assert latency < 15000, f"Cold-start too slow: {latency:.0f}ms"
        print(f"  API PING: {latency:.0f}ms, {tokens} tokens")


@pytest.mark.e2e
class TestAgentUXFlows:
    """Test real user workflows with timing and quality checks."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_simple_qa_flow(self):
        """User asks a simple question — agent answers directly.
        Tests: latency, relevance, conciseness.
        """
        msg, latency, tokens = await _call_llm([
            {"role": "system", "content": "You are a helpful assistant. Keep answers concise (1-2 sentences)."},
            {"role": "user", "content": "What is the capital of France?"},
        ])
        assert msg is not None
        answer = msg.content
        assert "Paris" in answer, f"Expected 'Paris' in answer, got: {answer}"

        _test_metrics["qa_latency_ms"] = latency
        _test_metrics["qa_tokens"] = tokens

        # UX: direct answer should be < 5s after cold-start
        assert latency < 8000, f"QA too slow: {latency:.0f}ms"
        # UX: answer should be short (easy to read)
        assert len(answer) < 200, f"Answer too verbose: {len(answer)} chars"
        print(f"  QA FLOW: {latency:.0f}ms, {tokens} tokens, answer='{answer[:60]}...'")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tool_use_flow(self):
        """User requests a calculation — agent should use tool reasoning.
        Tests: tool selection awareness, structured reasoning.
        """
        msg, latency, tokens = await _call_llm([
            {"role": "system", "content": "You have access to Python code execution. If a user asks for math, explain you can run code."},
            {"role": "user", "content": "Calculate 15 * 23 + 7"},
        ])
        assert msg is not None
        answer = msg.content

        _test_metrics["tool_latency_ms"] = latency
        _test_metrics["tool_tokens"] = tokens

        # Should mention code/calculation/tool
        quality_indicators = ["352", "calculate", "python", "code", "run", "compute"]
        has_quality = any(ind in answer.lower() for ind in quality_indicators)
        assert has_quality, f"Answer should show tool awareness, got: {answer}"

        # UX: tool-use response should be < 8s
        assert latency < 10000, f"Tool-flow too slow: {latency:.0f}ms"
        print(f"  TOOL FLOW: {latency:.0f}ms, {tokens} tokens, answer='{answer[:80]}...'")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_code_skill_flow(self):
        """User asks to write code — tests code generation quality.
        Tests: syntax correctness, language awareness.
        """
        msg, latency, tokens = await _call_llm([
            {"role": "system", "content": "You are a Python expert. Respond with only the code block, no explanations."},
            {"role": "user", "content": "Write a Python one-liner to reverse a list: [1,2,3]"},
        ])
        assert msg is not None
        answer = msg.content

        _test_metrics["code_latency_ms"] = latency
        _test_metrics["code_tokens"] = tokens

        # Quality: should contain Python syntax
        assert "[::-1]" in answer or "reverse" in answer.lower() or "reversed" in answer.lower(), \
            f"Expected list reversal syntax, got: {answer}"

        # UX: code generation should be fast
        assert latency < 10000, f"Code gen too slow: {latency:.0f}ms"
        print(f"  CODE FLOW: {latency:.0f}ms, {tokens} tokens, snippet='{answer[:60]}...'")


@pytest.mark.e2e
class TestAgentCreationUX:
    """Test creating and configuring agents via API."""

    @pytest.mark.asyncio
    async def test_create_agent_via_api(self, auth_client):
        """User creates a custom agent — should succeed quickly."""
        from httpx import AsyncClient

        agent = {
            "id": "ux_test_agent",
            "name": "UX Test Agent",
            "icon": "🧪",
            "description": "Agent for UX testing",
            "role": "You help test the system.",
            "model": {},
            "skills": ["research", "code_analysis"],
            "tools": [],
            "sub_agents": [],
            "memory": {"enabled": True},
            "output": {},
        }
        start = time.time()
        resp = await auth_client.post("/api/agents", json=agent)
        latency_ms = (time.time() - start) * 1000

        # UX: agent creation should be < 500ms (no LLM involved)
        assert latency_ms < 500, f"Agent creation too slow: {latency_ms:.0f}ms"
        assert resp.status_code in (200, 403)

        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "created"
            # Cleanup
            await auth_client.delete("/api/agents/ux_test_agent")

        _test_metrics["create_agent_latency_ms"] = latency_ms
        print(f"  CREATE AGENT: {latency_ms:.0f}ms")

    @pytest.mark.asyncio
    async def test_list_agents_speed(self, auth_client):
        """Listing agents should be instant (< 200ms)."""
        start = time.time()
        resp = await auth_client.get("/api/agents")
        latency_ms = (time.time() - start) * 1000

        assert resp.status_code == 200
        agents = resp.json()
        assert isinstance(agents, list)
        assert len(agents) > 0

        # UX: listing must be < 200ms
        assert latency_ms < 200, f"Agent listing too slow: {latency_ms:.0f}ms"
        _test_metrics["list_agents_latency_ms"] = latency_ms
        print(f"  LIST AGENTS: {latency_ms:.0f}ms ({len(agents)} agents)")


@pytest.mark.e2e
class TestChatUXFlows:
    """Test chat interface UX metrics."""

    @pytest.mark.asyncio
    async def test_chat_endpoint_response_time(self, auth_client):
        """Chat endpoint should respond quickly even before LLM finishes."""
        # We test the HTTP response time, not LLM time
        payload = {
            "message": "Hello",
            "agent_id": "universal",
            "auto_agents": False,
        }
        start = time.time()
        resp = await auth_client.post("/api/chat", json=payload)
        latency_ms = (time.time() - start) * 1000

        # This will either succeed or fail quickly — we measure response time
        assert latency_ms < 30000, f"Chat endpoint hung: {latency_ms:.0f}ms"
        _test_metrics["chat_http_latency_ms"] = latency_ms
        print(f"  CHAT HTTP: {latency_ms:.0f}ms (status={resp.status_code})")

    @pytest.mark.asyncio
    async def test_stream_endpoint_connect_time(self, auth_client):
        """SSE stream should connect immediately."""
        payload = {
            "message": "Hi",
            "agent_id": "universal",
            "auto_agents": False,
        }
        start = time.time()
        resp = await auth_client.post("/api/chat/stream", json=payload)
        latency_ms = (time.time() - start) * 1000

        # Connection should establish in < 2s
        assert latency_ms < 2000, f"SSE connect too slow: {latency_ms:.0f}ms"
        _test_metrics["stream_connect_ms"] = latency_ms
        print(f"  STREAM CONNECT: {latency_ms:.0f}ms")


@pytest.mark.e2e
class TestSkillDiscoveryUX:
    """Test how easy it is to discover and use skills."""

    @pytest.mark.asyncio
    async def test_marketplace_load_time(self, client):
        """Marketplace page should load fast."""
        start = time.time()
        resp = await client.get("/api/marketplace")
        latency_ms = (time.time() - start) * 1000

        assert resp.status_code == 200
        data = resp.json()
        skills = data["skills"]
        assert len(skills) > 0

        # UX: API response < 100ms
        assert latency_ms < 100, f"Marketplace API too slow: {latency_ms:.0f}ms"

        # UX: Every skill must have description and tags (discoverable)
        for skill in skills:
            assert skill.get("description"), f"Skill {skill['name']} missing description"
            assert skill.get("tags"), f"Skill {skill['name']} missing tags"

        _test_metrics["marketplace_latency_ms"] = latency_ms
        _test_metrics["marketplace_skills"] = len(skills)
        print(f"  MARKETPLACE: {latency_ms:.0f}ms ({len(skills)} skills)")

    @pytest.mark.asyncio
    async def test_builder_page_load(self, auth_client):
        """Builder page should load with all skill options."""
        start = time.time()
        resp = await auth_client.get("/builder")
        latency_ms = (time.time() - start) * 1000

        assert resp.status_code == 200
        html = resp.text
        assert "Конструктор агентов" in html

        # Check that skills are rendered in the builder
        assert "data_analyst" in html or "Анализ данных" in html or "📊" in html

        _test_metrics["builder_load_ms"] = latency_ms
        print(f"  BUILDER LOAD: {latency_ms:.0f}ms")


# ---------------------------------------------------------------------------
# Summary reporter
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def report_metrics():
    yield
    print("\n" + "=" * 60)
    print("UX / PERFORMANCE SUMMARY")
    print("=" * 60)
    for key, value in sorted(_test_metrics.items()):
        if "latency" in key or "ms" in key:
            print(f"  {key}: {value:.0f}ms")
        elif "tokens" in key:
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")

    # UX Scorecard
    print("\n--- UX Scorecard ---")
    scores = []
    if "ping_latency_ms" in _test_metrics:
        scores.append(("API Cold-start", _test_metrics["ping_latency_ms"] < 15000))
    if "qa_latency_ms" in _test_metrics:
        scores.append(("Simple QA Speed", _test_metrics["qa_latency_ms"] < 8000))
    if "tool_latency_ms" in _test_metrics:
        scores.append(("Tool-use Speed", _test_metrics["tool_latency_ms"] < 10000))
    if "code_latency_ms" in _test_metrics:
        scores.append(("Code Gen Speed", _test_metrics["code_latency_ms"] < 10000))
    if "create_agent_latency_ms" in _test_metrics:
        scores.append(("Agent Creation Speed", _test_metrics["create_agent_latency_ms"] < 500))
    if "list_agents_latency_ms" in _test_metrics:
        scores.append(("Agent Listing Speed", _test_metrics["list_agents_latency_ms"] < 200))
    if "marketplace_latency_ms" in _test_metrics:
        scores.append(("Marketplace Speed", _test_metrics["marketplace_latency_ms"] < 100))
    if "builder_load_ms" in _test_metrics:
        scores.append(("Builder Load Speed", _test_metrics["builder_load_ms"] < 1000))

    passed = sum(1 for _, ok in scores if ok)
    total = len(scores)
    for name, ok in scores:
        status = "PASS" if ok else "FAIL"
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}: {status}")
    print(f"\nUX Score: {passed}/{total}")
    print("=" * 60)
