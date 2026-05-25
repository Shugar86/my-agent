"""Security hardening tests."""

import os
from unittest.mock import patch

import pytest

from web.security import is_public_path, resolve_rate_limit


class TestPublicPaths:
    """Auth whitelist policy."""

    def test_login_public(self):
        assert is_public_path("/api/login", "POST") is True

    def test_marketplace_get_public(self):
        assert is_public_path("/api/marketplace", "GET") is True

    def test_marketplace_install_requires_auth(self):
        assert is_public_path("/api/marketplace/install/sql_db", "POST") is False

    def test_workflow_templates_get_public(self):
        assert is_public_path("/api/workflow-templates", "GET") is True

    def test_workflow_templates_post_requires_auth(self):
        assert is_public_path("/api/workflow-templates", "POST") is False

    def test_workflow_run_requires_auth(self):
        assert is_public_path("/api/workflows/abc/run", "POST") is False

    def test_webhook_public(self):
        assert is_public_path("/api/workflows/webhook/wf-1", "POST") is True


class TestRateLimitRules:
    """Expensive endpoint rate-limit mapping."""

    def test_chat_stream_limited(self):
        rule = resolve_rate_limit("/api/chat/stream", "POST")
        assert rule is not None
        assert rule.limit == 20

    def test_workflow_run_limited(self):
        rule = resolve_rate_limit("/api/workflows/wf-1/run", "POST")
        assert rule is not None
        assert rule.action == "workflow_run"

    def test_health_not_limited(self):
        assert resolve_rate_limit("/api/health", "GET") is None


class TestSelfDevProduction:
    """Self-modification must be blocked in production."""

    def test_skill_allowed_false_in_production(self):
        with patch.dict(os.environ, {"ENV": "production", "ENABLE_SELF_DEV": "false"}):
            import importlib
            import core.skill_loader as sl_mod
            importlib.reload(sl_mod)
            assert sl_mod._skill_allowed("self_dev") is False
            assert sl_mod._skill_allowed("gmail") is True

    def test_write_source_blocked_in_production(self):
        with patch.dict(os.environ, {"ENV": "production", "ENABLE_SELF_DEV": "false"}):
            import importlib
            import skills.self_dev.skill as sd
            importlib.reload(sd)
            result = sd.write_source("README.md", "hack", approved=True)
            assert result["success"] is False
            assert "disabled" in result["error"].lower()

    def test_register_tools_noop_in_production(self):
        with patch.dict(os.environ, {"ENV": "production", "ENABLE_SELF_DEV": "false"}):
            import importlib
            import skills.self_dev.skill as sd
            from core.tool_registry import registry
            importlib.reload(sd)
            sd.register_tools()
            assert not registry.has("write_source")
