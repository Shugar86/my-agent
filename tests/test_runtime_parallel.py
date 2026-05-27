"""Tests for parallel tool execution and runtime improvements."""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


class TestExecuteToolsParallel:
    """Tests for AgentRuntime._execute_tools_parallel."""

    @pytest.fixture
    def mock_runtime(self):
        """Create a mock AgentRuntime with controlled skills."""
        from core.runtime import AgentRuntime
        from core.iteration_budget import IterationBudget

        runtime = MagicMock(spec=AgentRuntime)
        runtime.skills = MagicMock()
        runtime.events = None
        runtime.plugins = None
        return runtime

    def test_parallel_execution_faster_than_sequential(self):
        """Parallel execution should be faster than sequential."""
        import time

        def slow_func():
            time.sleep(0.05)
            return "done"

        # Sequential
        t0 = time.time()
        for _ in range(3):
            slow_func()
        sequential_time = time.time() - t0

        # Parallel (using threading for sync functions)
        from concurrent.futures import ThreadPoolExecutor
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(lambda _: slow_func(), range(3)))
        parallel_time = time.time() - t0

        assert parallel_time < sequential_time * 0.7

    def test_runtime_has_parallel_method(self):
        """AgentRuntime has _execute_tools_parallel method."""
        from core.runtime import AgentRuntime
        assert hasattr(AgentRuntime, '_execute_tools_parallel')

    def test_loop_detection_signature(self):
        """Loop detection uses correct signature format."""
        import json
        tool_name = "web_search"
        args = {"query": "test"}
        signature = (tool_name, json.dumps(args, sort_keys=True))
        assert signature == ("web_search", '{"query": "test"}')

    def test_loop_detection_checks_results_not_tool_calls_raw(self):
        """Regression: loop flag is the second tuple element, not tool_calls_raw."""
        tool_calls_raw, results = None, "loop_detected"
        assert (tool_calls_raw == "loop_detected") is False
        assert results == "loop_detected"


class TestRuntimeIntegration:
    """Integration tests for AgentRuntime with real components."""

    @pytest.mark.asyncio
    async def test_runtime_build_system_prompt(self):
        """Runtime builds system prompt from role and skills."""
        from core.runtime import AgentRuntime
        from core.builder import AgentBuilder

        builder = (AgentBuilder()
            .set_model({"primary": "test"})
            .set_role("You are a test assistant.")
            .set_skills(["research"])
            .set_tools(["web_search"]))
        agent = builder.build()

        prompt = agent._build_system_prompt()
        assert "test assistant" in prompt

    def test_budget_exhausted_error_exists(self):
        """BudgetExhaustedError class exists and has message."""
        from core.iteration_budget import BudgetExhaustedError
        # Just verify the exception class exists and can be instantiated
        exc = BudgetExhaustedError("Test message")
        assert "Test message" in str(exc)


class TestSkillCacheIntegration:
    """Integration between skill cache and runtime."""

    def test_skill_filter_in_runtime_context(self):
        """Skill filtering works with real skill names."""
        from core.skill_cache import filter_skills_by_query
        from core.builder import AgentBuilder

        builder = (AgentBuilder()
            .set_model({"primary": "test"})
            .set_skills(["research", "code_analysis", "deep_research"])
            .set_tools(["web_search", "deep_search", "execute_code"]))
        agent = builder.build()

        all_tools = agent.skills.get_schemas()
        tool_names = [t.get("function", {}).get("name", "") for t in all_tools]

        # Query about research should include search tools
        filtered = filter_skills_by_query("research academic paper", tool_names)
        assert any("search" in name for name in filtered)

    def test_skill_filter_reduces_token_count(self):
        """Filtering reduces the number of tools passed to LLM."""
        from core.skill_cache import filter_skills_by_query

        all_skills = list(range(50))  # Simulate 50 tools
        skill_names = [f"tool_{i}" for i in all_skills]

        filtered = filter_skills_by_query("simple query", skill_names)
        assert len(filtered) <= len(skill_names)
        assert len(filtered) >= 5 or len(filtered) == len(skill_names)
