"""Shared pytest fixtures for web API tests."""
import os

import pytest
from httpx import ASGITransport, AsyncClient

from core.auth import create_access_token
from web.server import app, user_manager, _init_agent_runtime


@pytest.fixture
async def client():
    os.makedirs("data", exist_ok=True)
    os.environ["ENV"] = "test"
    await user_manager.connect()
    _init_agent_runtime()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as c:
        yield c
    await user_manager.close()


@pytest.fixture
async def auth_client(client):
    """Authenticated client with valid session cookie."""
    token = create_access_token({"sub": "testuser", "user_id": "u_test123", "role": "user"})
    client.cookies.set("access_token", token)
    return client
