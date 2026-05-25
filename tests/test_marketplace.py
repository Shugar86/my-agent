"""Marketplace and builder API tests."""
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
    token = create_access_token({"sub": "testuser", "user_id": "u_test123", "role": "user"})
    client.cookies.set("access_token", token)
    return client


class TestMarketplaceAPI:
    @pytest.mark.asyncio
    async def test_marketplace_returns_skills(self, client):
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


class TestBuilderPage:
    @pytest.mark.asyncio
    async def test_builder_page_redirects_when_unauth(self, client):
        response = await client.get("/builder", follow_redirects=False)
        assert response.status_code in (307, 401)

    @pytest.mark.asyncio
    async def test_builder_page_loads_when_auth(self, auth_client):
        response = await auth_client.get("/builder")
        assert response.status_code == 200
        assert "Конструктор агентов" in response.text


class TestStatsPageIntegration:
    @pytest.mark.asyncio
    async def test_stats_returns_numbers_authenticated(self, auth_client):
        response = await auth_client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["agents"], int)
        assert isinstance(data["skills"], int)
        assert isinstance(data["tools"], int)
