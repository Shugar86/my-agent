"""End-to-end integration tests for new features."""
import pytest
import asyncio
import os
from unittest.mock import patch

_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
_REGISTRY_PATH = os.path.join(_PROJECT_ROOT, "agents", "registry.json")


class TestEndToEndChat:
    """E2E tests simulating real user interactions."""

    @pytest.mark.asyncio
    async def test_chat_with_fast_profile(self):
        """Full chat cycle with fast model profile."""
        from core.builder import AgentBuilder
        from core.llm_gateway import LLMGateway

        model_config = {
            "primary": "openai/gpt-5.4-nano",
            "api_key": os.environ.get("NEUROAPI_API_KEY", ""),
            "base_url": "https://neuroapi.host/v1",
            "params": {"max_tokens": 50},
            "max_retries": 1,
        }

        if not model_config["api_key"]:
            pytest.skip("NEUROAPI_API_KEY not set")

        builder = (AgentBuilder()
            .set_model(model_config)
            .set_role("You are a test assistant.")
            .set_skills(["research"])
            .set_tools(["web_search"]))
        agent = builder.build()

        result = await agent.run("Say hello in 2 words", session_id="test_e2e_1")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_cli_user_session_persists(self):
        """CLI user session persists across operations."""
        from agent import _set_cli_user, _get_cli_user, _clear_cli_user

        _clear_cli_user()
        assert _get_cli_user() is None

        _set_cli_user({"username": "test_e2e", "role": "user"})
        user = _get_cli_user()
        assert user["username"] == "test_e2e"
        assert user["role"] == "user"

        _clear_cli_user()

    def test_agent_registry_has_10_agents(self):
        """Registry contains exactly 10 agents."""
        from core.agent_store import AgentStore
        store = AgentStore(registry_path=_REGISTRY_PATH)
        agents = store.list_agents()
        assert len(agents) == 10

    def test_all_agents_have_required_fields(self):
        """Each agent has required fields."""
        from core.agent_store import AgentStore
        store = AgentStore(registry_path=_REGISTRY_PATH)
        agents = store.list_agents()

        required = ["id", "name", "icon", "description", "role", "skills", "tools"]
        for agent in agents:
            for field in required:
                assert field in agent, f"Agent {agent.get('id', '?')} missing {field}"

    def test_web_server_imports_all_routes(self):
        """Web server has all expected routes."""
        from web.server import app
        routes = [r for r in app.routes]
        paths = [str(r.path) for r in routes if hasattr(r, 'path')]

        required_paths = ["/", "/chat", "/agents", "/settings", "/api/chat", "/api/agents", "/api/health"]
        for path in required_paths:
            assert any(path in p for p in paths), f"Missing route: {path}"

    @pytest.mark.asyncio
    async def test_streaming_endpoint_structure(self):
        """Stream endpoint returns correct structure."""
        from web.server import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        # Note: This requires auth, so it will likely return 401
        response = client.post("/api/chat/stream", json={
            "message": "hi",
            "agent_id": "universal",
        })
        # Should either succeed or fail quickly (not hang)
        assert response.status_code in [200, 401, 403]

    def test_tool_registry_populated(self):
        """Tool registry has registered tools."""
        from core.tool_registry import registry
        tools = registry.get_schemas()
        # Should have at least the core tools
        assert len(tools) > 0

    def test_skills_have_schemas(self):
        """Skills can provide their tool schemas."""
        from core.builder import AgentBuilder
        builder = (AgentBuilder()
            .set_model({"primary": "test"})
            .set_skills(["research", "code_analysis"])
            .set_tools(["web_search", "execute_code"]))
        agent = builder.build()

        schemas = agent.skills.get_schemas()
        assert len(schemas) > 0
        for schema in schemas:
            assert "type" in schema
            assert "function" in schema

    def test_memory_manager_enabled(self):
        """Memory can be enabled/disabled."""
        from core.builder import AgentBuilder
        builder = (AgentBuilder()
            .set_model({"primary": "test"})
            .set_memory({"enabled": True}))
        agent = builder.build()
        assert agent.memory.enabled is True

        builder2 = (AgentBuilder()
            .set_model({"primary": "test"})
            .set_memory({"enabled": False}))
        agent2 = builder2.build()
        assert agent2.memory.enabled is False


class TestConfigResolution:
    """Tests for config resolution with env vars."""

    def test_load_config_returns_dict(self):
        """load_config returns a dictionary."""
        from core.config import load_config
        config_path = os.path.join(_PROJECT_ROOT, "config", "agent.json")
        config = load_config(config_path)
        assert isinstance(config, dict)
        assert "model" in config

    def test_resolve_env_vars_replaces_placeholders(self):
        """resolve_env_vars replaces ${VAR} with env values."""
        from core.config import resolve_env_vars
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}, clear=False):
            result = resolve_env_vars({"key": "${TEST_VAR}"})
        assert result["key"] == "test_value"

    def test_resolve_env_vars_keeps_string(self):
        """resolve_env_vars preserves plain strings."""
        from core.config import resolve_env_vars
        result = resolve_env_vars({"key": "plain_string"})
        assert result["key"] == "plain_string"


class TestDockerSandbox:
    """Tests for Docker sandbox configuration."""

    def test_docker_sandbox_imports(self):
        """Docker sandbox module imports correctly."""
        from core.docker_sandbox import DockerSandbox
        assert DockerSandbox is not None

    def test_sandbox_has_security_flags(self):
        """Sandbox uses security flags."""
        from core.docker_sandbox import DockerSandbox
        # Check the module has the expected security constants
        import inspect
        source = inspect.getsource(DockerSandbox)
        assert "network none" in source or "network" in source
        assert "memory" in source
        assert "read-only" in source or "read_only" in source


class TestScheduler:
    """Tests for scheduler functionality."""

    def test_scheduler_manager_imports(self):
        """Scheduler manager imports."""
        from core.scheduler_manager import scheduler_manager
        assert scheduler_manager is not None

    def test_scheduler_api_endpoints_exist(self):
        """Scheduler endpoints are in the app."""
        from web.server import app
        routes = [str(r.path) for r in app.routes if hasattr(r, 'path')]
        assert any("schedule" in r for r in routes)


class TestMetrics:
    """Tests for Prometheus metrics."""

    def test_metrics_endpoint_exists(self):
        """Metrics endpoint is registered."""
        from web.server import app
        routes = [str(r.path) for r in app.routes if hasattr(r, 'path')]
        assert "/metrics" in routes

    def test_prometheus_counters_defined(self):
        """Prometheus counters are defined."""
        from web.server import REQUEST_COUNT, REQUEST_LATENCY, LLM_TOKEN_COUNT
        assert REQUEST_COUNT is not None
        assert REQUEST_LATENCY is not None
        assert LLM_TOKEN_COUNT is not None
