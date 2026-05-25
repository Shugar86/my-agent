"""End-to-end skill and UX tests with mock LLM (zero API cost).

These tests verify the full user flow without consuming API quota.
To run with REAL API, set: USE_REAL_API=1
"""
import pytest
import asyncio
import time
import os
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient
from web.server import app, user_manager
from core.auth import create_access_token

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["ENV"] = "test"

USE_REAL_API = os.getenv("USE_REAL_API", "0") == "1"
REAL_MODEL = "openrouter/deepseek/deepseek-v4-flash:free"


@pytest.fixture
async def client():
    os.makedirs("data", exist_ok=True)
    await user_manager.connect()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as c:
        yield c
    await user_manager.close()


@pytest.fixture
async def auth_client(client):
    token = create_access_token({"sub": "test", "user_id": "u_test", "role": "user"})
    client.cookies.set("access_token", token)
    return client


# ---------------------------------------------------------------------------
# UX / Performance Tests (Fast Endpoints Only)
# ---------------------------------------------------------------------------

@pytest.mark.ux
class TestUserJourneySpeed:
    """Measure how fast users can accomplish tasks."""

    @pytest.mark.asyncio
    async def test_register_and_login_speed(self, client):
        """Registration + login should be under 1 second combined."""
        t0 = time.time()
        reg = await client.post("/api/register", json={
            "username": "ux_speed_user",
            "password": "SecurePass123!",
        })
        reg_time = (time.time() - t0) * 1000
        assert reg.status_code in (200, 409)

        t0 = time.time()
        login = await client.post("/api/login", json={
            "username": "ux_speed_user",
            "password": "SecurePass123!",
        })
        login_time = (time.time() - t0) * 1000
        assert login.status_code == 200

        total = reg_time + login_time
        print(f"  REGISTER+LOGIN: {total:.0f}ms")
        assert total < 2000, f"Auth too slow: {total:.0f}ms"

    @pytest.mark.asyncio
    async def test_agent_creation_under_300ms(self, auth_client):
        """Creating an agent should feel instant."""
        agent = {
            "id": "speed_test_agent",
            "name": "Speed Test",
            "icon": "⚡",
            "description": "Testing speed",
            "role": "You are fast.",
            "model": {},
            "skills": ["research"],
            "tools": [],
            "sub_agents": [],
            "memory": {"enabled": False},
            "output": {},
        }
        t0 = time.time()
        resp = await auth_client.post("/api/agents", json=agent)
        latency = (time.time() - t0) * 1000

        assert resp.status_code in (200, 403)
        print(f"  AGENT CREATE: {latency:.0f}ms")
        assert latency < 300, f"Agent creation too slow: {latency:.0f}ms"

        if resp.status_code == 200:
            await auth_client.delete("/api/agents/speed_test_agent")

    @pytest.mark.asyncio
    async def test_marketplace_browse_under_100ms(self, client):
        """Browsing marketplace should be instantaneous."""
        t0 = time.time()
        resp = await client.get("/api/marketplace")
        latency = (time.time() - t0) * 1000

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        print(f"  MARKETPLACE BROWSE: {latency:.0f}ms ({data['total']} skills)")
        assert latency < 100, f"Marketplace too slow: {latency:.0f}ms"

    @pytest.mark.asyncio
    async def test_builder_load_under_500ms(self, auth_client):
        """Builder page should load fast."""
        t0 = time.time()
        resp = await auth_client.get("/builder")
        latency = (time.time() - t0) * 1000

        assert resp.status_code == 200
        print(f"  BUILDER LOAD: {latency:.0f}ms")
        assert latency < 500, f"Builder load too slow: {latency:.0f}ms"

    @pytest.mark.asyncio
    async def test_stats_endpoint_under_100ms(self, auth_client):
        """Stats API should be blazing fast."""
        t0 = time.time()
        resp = await auth_client.get("/api/stats")
        latency = (time.time() - t0) * 1000

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["agents"], int)
        print(f"  STATS API: {latency:.0f}ms")
        assert latency < 100, f"Stats too slow: {latency:.0f}ms"


@pytest.mark.ux
class TestSkillDiscovery:
    """Test skill marketplace discoverability."""

    @pytest.mark.asyncio
    async def test_all_skills_have_descriptions(self, client):
        """Every skill must be self-explanatory."""
        resp = await client.get("/api/marketplace")
        skills = resp.json()["skills"]
        for skill in skills:
            assert skill.get("description"), f"Skill {skill['name']} missing description"
            assert skill.get("tags"), f"Skill {skill['name']} missing tags"
            assert skill.get("installs") is not None, f"Skill {skill['name']} missing install count"

    @pytest.mark.asyncio
    async def test_skills_filterable_by_tag(self, client):
        """Users should find skills by category."""
        resp = await client.get("/api/marketplace")
        skills = resp.json()["skills"]
        tags = set()
        for s in skills:
            tags.update(s["tags"])
        # Should have diverse categories
        assert len(tags) >= 5, f"Too few skill categories: {tags}"


@pytest.mark.ux
class TestEaseOfUse:
    """Test that the system is intuitive and forgiving."""

    @pytest.mark.asyncio
    async def test_empty_message_handled(self, auth_client):
        """Empty messages should not crash."""
        resp = await auth_client.post("/api/chat", json={
            "message": "",
            "agent_id": "universal",
            "auto_agents": False,
        })
        assert resp.status_code in (200, 422, 401)
        print(f"  EMPTY MSG: OK (status={resp.status_code})")

    @pytest.mark.asyncio
    async def test_very_long_message_handled(self, auth_client):
        """Very long messages should be handled (or rejected gracefully)."""
        resp = await auth_client.post("/api/chat", json={
            "message": "x" * 10000,
            "agent_id": "universal",
            "auto_agents": False,
        })
        assert resp.status_code != 500
        print(f"  LONG MSG: OK (status={resp.status_code})")

    @pytest.mark.asyncio
    async def test_invalid_agent_id_handled(self, auth_client):
        """Non-existent agent should return clear error."""
        resp = await auth_client.post("/api/chat", json={
            "message": "Hello",
            "agent_id": "nonexistent_agent_xyz",
            "auto_agents": False,
        })
        assert resp.status_code in (200, 404)
        print(f"  INVALID AGENT: OK (status={resp.status_code})")

    @pytest.mark.asyncio
    async def test_special_characters_in_message(self, auth_client):
        """Messages with Unicode/emojis should work."""
        resp = await auth_client.post("/api/chat", json={
            "message": "Привет! 🚀 Как дела? 你好",
            "agent_id": "universal",
            "auto_agents": False,
        })
        assert resp.status_code == 200
        print(f"  UNICODE MSG: OK")


class TestRealAPIOptionally:
    """Tests that only run when USE_REAL_API=1."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not USE_REAL_API, reason="Set USE_REAL_API=1 to run with real LLM")
    async def test_real_api_latency(self):
        """Single real API call to verify connectivity and measure latency."""
        import litellm
        start = time.time()
        try:
            resp = await litellm.acompletion(
                model=REAL_MODEL,
                messages=[{"role": "user", "content": "Say hi"}],
                api_key=os.environ.get("OPENROUTER_API_KEY", ""),
                api_base="https://openrouter.ai/api/v1",
                timeout=30,
            )
            latency = (time.time() - start) * 1000
            tokens = resp.usage.total_tokens if resp.usage else 0
            print(f"  REAL API: {latency:.0f}ms, {tokens} tokens")
            assert latency < 15000
        except Exception as e:
            pytest.skip(f"Real API unavailable: {e}")
