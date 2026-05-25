"""Tests for Redis session cache and response cache."""
import pytest
import json

pytestmark = pytest.mark.asyncio


class MockRedisClient:
    """Mock Redis client for testing cache logic."""

    def __init__(self):
        self.data = {}
        self.available = True

    async def set(self, key, value, expire=None):
        self.data[key] = value
        return True

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, key):
        self.data.pop(key, None)
        return True

    async def setex(self, key, expire, value):
        self.data[key] = value
        return True

    async def get_cached_response(self, key):
        return self.data.get(f"cache:{key}")

    async def cache_response(self, key, value, expire=300):
        self.data[f"cache:{key}"] = value
        return True

    async def check_rate_limit(self, key, limit, window):
        current = self.data.get(key, 0) + 1
        self.data[key] = current
        return current <= limit, max(0, limit - current)

    def pipeline(self):
        return MockPipeline(self)


class MockPipeline:
    """Mock Redis pipeline."""

    def __init__(self, client):
        self.client = client
        self.commands = []

    def incr(self, key):
        self.commands.append(("incr", key))
        return self

    def expire(self, key, seconds):
        self.commands.append(("expire", key, seconds))
        return self

    async def execute(self):
        results = []
        for cmd in self.commands:
            if cmd[0] == "incr":
                key = cmd[1]
                current = self.client.data.get(key, 0) + 1
                self.client.data[key] = current
                results.append(current)
            elif cmd[0] == "expire":
                results.append(True)
        self.commands = []
        return results


@pytest.fixture
def mock_redis(monkeypatch):
    client = MockRedisClient()
    from core import redis_client as rc
    monkeypatch.setattr(rc.redis_client, "_client", client)
    monkeypatch.setattr(rc.redis_client, "_available", True)
    return client


async def test_session_cache_roundtrip(mock_redis):
    """Test storing and retrieving session messages."""
    from core.session_cache import SessionCache

    session_id = "test_session_123"
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]

    # Store
    result = await SessionCache.set_messages(session_id, messages)
    assert result is True

    # Retrieve
    retrieved = await SessionCache.get_messages(session_id)
    assert len(retrieved) == 2
    assert retrieved[0]["content"] == "hello"


async def test_session_cache_append(mock_redis):
    """Test appending message to session."""
    from core.session_cache import SessionCache

    session_id = "test_append_456"
    await SessionCache.set_messages(session_id, [{"role": "user", "content": "start"}])

    await SessionCache.append_message(session_id, {"role": "assistant", "content": "reply"})

    messages = await SessionCache.get_messages(session_id)
    assert len(messages) == 2
    assert messages[1]["content"] == "reply"


async def test_session_cache_metadata(mock_redis):
    """Test session metadata storage."""
    from core.session_cache import SessionCache

    session_id = "test_meta_789"
    meta = {"agent_id": "universal", "model": "fast", "created_at": "2024-01-01"}

    await SessionCache.set_metadata(session_id, meta)
    retrieved = await SessionCache.get_metadata(session_id)

    assert retrieved is not None
    assert retrieved["agent_id"] == "universal"
    assert retrieved["model"] == "fast"


async def test_response_cache_hit(mock_redis):
    """Test response cache stores and retrieves LLM responses."""
    from core.session_cache import ResponseCache

    model = "gpt-test"
    prompt = "What is 2+2?"
    response = "4"

    # Cache miss initially
    cached = await ResponseCache.get(model, prompt)
    assert cached is None

    # Store
    await ResponseCache.set(model, prompt, response)

    # Cache hit
    cached = await ResponseCache.get(model, prompt)
    assert cached == "4"


async def test_response_cache_different_tools(mock_redis):
    """Test cache key depends on tools list."""
    from core.session_cache import ResponseCache

    model = "gpt-test"
    prompt = "analyze"

    await ResponseCache.set(model, prompt, "result1", tools=["tool_a"])
    await ResponseCache.set(model, prompt, "result2", tools=["tool_b"])

    # Different tools -> different keys
    cached1 = await ResponseCache.get(model, prompt, tools=["tool_a"])
    cached2 = await ResponseCache.get(model, prompt, tools=["tool_b"])

    assert cached1 == "result1"
    assert cached2 == "result2"


async def test_rate_limiter_allowed(mock_redis):
    """Test rate limiter allows requests within limit."""
    from core.session_cache import RateLimiter

    allowed, remaining, reset = await RateLimiter.check(
        "user_1", "api_ask", limit=5, window=60
    )

    assert allowed is True
    assert remaining >= 0


async def test_rate_limiter_blocked(mock_redis):
    """Test rate limiter blocks requests over limit."""
    from core.session_cache import RateLimiter

    # Exhaust limit
    for _ in range(10):
        await RateLimiter.check("user_2", "api_ask", limit=3, window=60)

    allowed, remaining, reset = await RateLimiter.check(
        "user_2", "api_ask", limit=3, window=60
    )

    assert allowed is False
    assert remaining == 0


async def test_session_cache_clear(mock_redis):
    """Test clearing session removes data."""
    from core.session_cache import SessionCache

    session_id = "test_clear"
    await SessionCache.set_messages(session_id, [{"role": "user", "content": "test"}])

    messages = await SessionCache.get_messages(session_id)
    assert len(messages) == 1

    await SessionCache.clear(session_id)

    # After clear, should fallback to empty (SQLite fallback)
    messages = await SessionCache.get_messages(session_id)
    assert messages == []
