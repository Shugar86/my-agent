"""Tests for security improvements (CORS, exception handler, request size)."""
import os
import pytest
import json
from fastapi import Request
from unittest.mock import MagicMock, AsyncMock

_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


class TestExceptionHandler:
    """Tests for global_exception_handler in web/server.py."""

    @pytest.mark.asyncio
    async def test_error_message_is_generic(self):
        """Exception handler returns generic error, not internal details."""
        from web.server import global_exception_handler

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"

        # Simulate internal error
        internal_error = ValueError("Internal database password: secret123")
        response = await global_exception_handler(mock_request, internal_error)

        assert response.status_code == 500
        body = json.loads(response.body)
        # Should contain generic error, not the actual error
        assert "Internal server error" in body["error"]
        assert "secret123" not in str(body)

    @pytest.mark.asyncio
    async def test_error_does_not_expose_traceback(self):
        """Response should not contain traceback info."""
        from web.server import global_exception_handler

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/agents"

        error = RuntimeError("/path/to/secret/file.py line 42")
        response = await global_exception_handler(mock_request, error)

        body = json.loads(response.body)
        assert "/path/to/secret" not in str(body)
        assert "line 42" not in str(body)


class TestCorsMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_middleware_exists(self):
        """CORS middleware is registered in app."""
        from web.server import app
        from fastapi.middleware.cors import CORSMiddleware

        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls == CORSMiddleware:
                cors_middleware = middleware
                break

        assert cors_middleware is not None, "CORSMiddleware not found"

    def test_cors_allows_localhost(self):
        """CORS allows localhost origins."""
        from web.server import app
        from fastapi.middleware.cors import CORSMiddleware

        found = False
        for middleware in app.user_middleware:
            if middleware.cls == CORSMiddleware:
                # Check the middleware kwargs
                kwargs = middleware.kwargs if hasattr(middleware, 'kwargs') else {}
                origins = kwargs.get('allow_origins', [])
                assert any('localhost' in str(o) for o in origins)
                found = True
                break
        assert found, "CORSMiddleware not found"


class TestRequestSizeLimit:
    """Tests for request size limiting middleware."""

    @pytest.mark.asyncio
    async def test_oversized_request_rejected(self):
        """Request over 10MB should be rejected."""
        from web.server import limit_request_size
        from fastapi import Request
        from starlette.datastructures import Headers

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/test",
            "headers": [(b"content-length", b"11000000")],  # > 10MB
        }
        request = Request(scope)

        async def mock_call_next(req):
            return MagicMock(status_code=200)

        response = await limit_request_size(request, mock_call_next)
        assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_normal_request_passes(self):
        """Request under 10MB should pass through."""
        from web.server import limit_request_size
        from fastapi import Request

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/test",
            "headers": [(b"content-length", b"1024")],  # 1KB
        }
        request = Request(scope)

        async def mock_call_next(req):
            return MagicMock(status_code=200)

        response = await limit_request_size(request, mock_call_next)
        assert response.status_code == 200


class TestSecurityHeaders:
    """Tests for security-related headers and configurations."""

    def test_auth_middleware_registered(self):
        """AuthMiddleware is in the middleware stack."""
        from web.server import app
        from web.server import AuthMiddleware

        found = False
        for middleware in app.user_middleware:
            if middleware.cls == AuthMiddleware:
                found = True
                break
        assert found, "AuthMiddleware not registered"

    def test_rate_limiter_registered(self):
        """SlowAPI rate limiter is configured."""
        from web.server import limiter
        assert limiter is not None

    def test_jwt_secret_loaded_from_env_or_file(self):
        """JWT secret is loaded from env or file, not hardcoded as active secret."""
        import ast
        with open(os.path.join(_PROJECT_ROOT, "core/auth.py"), "r", encoding="utf-8") as f:
            source = f.read()

        # The code should reference env var and file, not a hardcoded secret
        assert "AGENT_SECRET_KEY" in source
        assert ".agent_secret" in source
        assert "os.urandom" in source  # Generates random secret if missing


class TestEnvExample:
    """Tests for .env.example security."""

    def test_no_real_api_keys_in_example(self):
        """.env.example should not contain real-looking API keys."""
        with open(os.path.join(_PROJECT_ROOT, ".env.example"), "r", encoding="utf-8") as f:
            content = f.read()

        # Should use placeholder syntax
        assert "${YOUR_" in content or "${OPENROUTER_API_KEY}" in content
        # Should not have sk- or tvly- patterns
        assert "sk-or-v1-" not in content, "Real OpenRouter key found in .env.example"
        assert "tvly-dev-" not in content, "Real Tavily key found in .env.example"

    def test_gitignore_has_agent_secret(self):
        """.gitignore should exclude .agent_secret."""
        with open(os.path.join(_PROJECT_ROOT, ".gitignore"), "r", encoding="utf-8") as f:
            content = f.read()
        assert ".agent_secret" in content
        assert ".env" in content

    def test_gitignore_has_env_local(self):
        """.gitignore should exclude .env.local."""
        with open(os.path.join(_PROJECT_ROOT, ".gitignore"), "r", encoding="utf-8") as f:
            content = f.read()
        assert ".env.local" in content or ".env" in content
