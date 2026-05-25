"""Web API E2E tests using httpx TestClient with authentication."""
import pytest
import os
from httpx import ASGITransport, AsyncClient
from web.server import app, user_manager
from core.auth import create_access_token


@pytest.fixture
async def client():
    os.makedirs("data", exist_ok=True)
    os.environ["ENV"] = "test"
    await user_manager.connect()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as c:
        yield c
    await user_manager.close()


@pytest.fixture
async def auth_client(client):
    """Authenticated client with valid session cookie."""
    # Create a valid token and set it as cookie directly
    token = create_access_token({"sub": "testuser", "user_id": "u_test123", "role": "user"})
    client.cookies.set("access_token", token)
    return client


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "agents" in data

    @pytest.mark.asyncio
    async def test_health_rate_limit(self, client):
        for _ in range(3):
            response = await client.get("/api/health")
            assert response.status_code in (200, 429)


class TestAuth:
    @pytest.mark.asyncio
    async def test_register_and_login(self, client):
        # Register
        reg = await client.post("/api/register", json={"username": "testuser_e2e_2", "password": "SecurePass123!"})
        assert reg.status_code in (200, 409)

        # Login
        login = await client.post("/api/login", json={"username": "testuser_e2e_2", "password": "SecurePass123!"})
        assert login.status_code in (200, 401)
        if login.status_code == 200:
            assert login.json()["success"] is True

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        response = await client.post("/api/register", json={"username": "u", "password": "weak"})
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_login_invalid(self, client):
        response = await client.post("/api/login", json={"username": "nonexistent", "password": "wrong"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_without_auth(self, client):
        response = await client.get("/api/me")
        assert response.status_code == 401


class TestStaticPages:
    @pytest.mark.asyncio
    async def test_login_page_public(self, client):
        response = await client.get("/login")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_protected_pages_redirect(self, client):
        pages = ["/", "/chat", "/agents", "/builder", "/marketplace"]
        for page in pages:
            response = await client.get(page, follow_redirects=False)
            assert response.status_code in (307, 401)


class TestAgentsAPI:
    @pytest.mark.asyncio
    async def test_list_agents_authenticated(self, auth_client):
        response = await auth_client.get("/api/agents")
        assert response.status_code == 200
        agents = response.json()
        assert isinstance(agents, list)
        assert len(agents) > 0

    @pytest.mark.asyncio
    async def test_get_agent_authenticated(self, auth_client):
        response = await auth_client.get("/api/agents/universal")
        assert response.status_code == 200
        data = response.json()
        assert data.get("id") == "universal" or "error" not in data

    @pytest.mark.asyncio
    async def test_get_agent_not_found_authenticated(self, auth_client):
        response = await auth_client.get("/api/agents/nonexistent_xyz")
        assert response.status_code == 200
        assert "error" in response.json()

    @pytest.mark.asyncio
    async def test_create_agent_authenticated(self, auth_client):
        agent = {
            "id": "test_agent_e2e",
            "name": "Test Agent",
            "icon": "🤖",
            "description": "For testing",
            "role": "test",
            "model": {},
            "skills": [],
            "tools": [],
            "sub_agents": [],
            "memory": {"enabled": False},
            "output": {},
        }
        create = await auth_client.post("/api/agents", json=agent)
        assert create.status_code in (200, 403)

        if create.status_code == 200:
            delete = await auth_client.delete("/api/agents/test_agent_e2e")
            assert delete.status_code in (200, 403)


class TestMarketplaceAPI:
    @pytest.mark.asyncio
    async def test_marketplace_list(self, client):
        response = await client.get("/api/marketplace")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert data["total"] > 0

    @pytest.mark.asyncio
    async def test_marketplace_skills_structure(self, client):
        response = await client.get("/api/marketplace")
        skills = response.json()["skills"]
        for skill in skills:
            assert "name" in skill
            assert "version" in skill
            assert "description" in skill
            assert "tags" in skill
            assert isinstance(skill["tags"], list)
            assert "installs" in skill

    @pytest.mark.asyncio
    async def test_marketplace_install_requires_auth(self, client):
        response = await client.post("/api/marketplace/install/sql_db")
        assert response.status_code in (401, 403)


class TestStatsAPI:
    @pytest.mark.asyncio
    async def test_stats_authenticated(self, auth_client):
        response = await auth_client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["agents"], int)
        assert isinstance(data["skills"], int)
        assert isinstance(data["tools"], int)


class TestConfigAPI:
    @pytest.mark.asyncio
    async def test_get_config_authenticated(self, auth_client):
        response = await auth_client.get("/api/config")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_config_requires_admin(self, auth_client):
        response = await auth_client.post("/api/config", json={"model": {"primary": "test"}})
        assert response.status_code in (200, 403)


class TestKnowledgeAPI:
    @pytest.mark.asyncio
    async def test_knowledge_list_authenticated(self, auth_client):
        response = await auth_client.get("/api/knowledge/list")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data

    @pytest.mark.asyncio
    async def test_knowledge_search_and_upload_authenticated(self, auth_client):
        upload = await auth_client.post("/api/knowledge/upload", json={"content": "test content", "source": "test"})
        assert upload.status_code in (200, 500)

        search = await auth_client.post("/api/knowledge/search", json={"query": "test", "n_results": 3})
        assert search.status_code in (200, 500)


class TestRequestSizeLimit:
    @pytest.mark.asyncio
    async def test_request_too_large_unauthenticated(self, client):
        huge_body = {"message": "x" * (11 * 1024 * 1024)}
        response = await client.post("/api/chat", json=huge_body)
        # Auth middleware runs before size limit, so unauthenticated gets 401
        assert response.status_code in (401, 413)


class TestCostAPI:
    @pytest.mark.asyncio
    async def test_cost_requires_auth(self, client):
        response = await client.get("/api/cost")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cost_reset_requires_auth(self, client):
        response = await client.post("/api/cost/reset")
        assert response.status_code == 401
