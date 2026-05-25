"""AI Evaluation framework tests."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from core.eval.prompt_eval import PromptEvaluator, PromptVariant
from core.eval.quality_metrics import (
    rouge_l, bleu_1, exact_match, semantic_similarity, compute_metrics
)
from core.eval.benchmarks import BENCHMARK_TASKS, get_benchmarks_by_category, get_all_categories


class TestPromptEvaluator:
    @pytest.fixture
    def evaluator(self):
        return PromptEvaluator({"primary": "gpt-4", "api_key": "test"})

    @pytest.mark.asyncio
    async def test_evaluate_returns_results(self, evaluator):
        variants = [
            PromptVariant("v1", "You are helpful", "Say hi", {}),
            PromptVariant("v2", "You are friendly", "Say hi", {}),
        ]
        mock_resp = MagicMock()
        mock_resp.content = "Hello!"
        judge_resp = MagicMock()
        judge_resp.content = "Score: 8"

        with patch("core.llm_gateway.LLMGateway.chat", new_callable=AsyncMock, side_effect=[mock_resp, mock_resp, judge_resp, judge_resp]):
            results = await evaluator.evaluate(variants)
            assert len(results) == 2
            assert all(r.score >= 0 for r in results)

    @pytest.mark.asyncio
    async def test_evaluate_latency_recorded(self, evaluator):
        variants = [PromptVariant("v1", "sys", "user", {})]
        mock_resp = MagicMock(content="OK")
        judge_resp = MagicMock(content="5")
        with patch("core.llm_gateway.LLMGateway.chat", new_callable=AsyncMock, side_effect=[mock_resp, judge_resp]):
            results = await evaluator.evaluate(variants)
            assert results[0].latency_ms >= 0

    @pytest.mark.asyncio
    async def test_run_benchmark(self, evaluator):
        tasks = [
            {"name": "t1", "prompt": "hi", "expected": ["hello"]},
        ]
        def factory(task):
            return [PromptVariant("v1", "sys", task["prompt"], {})]

        mock_resp = MagicMock(content="result")
        judge_resp = MagicMock(content="7")
        with patch("core.llm_gateway.LLMGateway.chat", new_callable=AsyncMock, side_effect=[mock_resp, judge_resp]):
            report = await evaluator.run_benchmark(tasks, factory)
            assert "summary" in report
            assert "winner" in report["summary"]


class TestQualityMetrics:
    def test_rouge_l_identical(self):
        assert rouge_l("hello world", "hello world") == 1.0

    def test_rouge_l_partial(self):
        score = rouge_l("hello world", "hello there world")
        assert 0 < score < 1.0

    def test_rouge_l_no_overlap(self):
        assert rouge_l("abc", "xyz") == 0.0

    def test_rouge_l_empty(self):
        assert rouge_l("", "hello") == 0.0

    def test_bleu_1_perfect(self):
        assert bleu_1("hello world", ["hello world"]) == 1.0

    def test_bleu_1_zero(self):
        assert bleu_1("", ["hello"]) == 0.0

    def test_exact_match_true(self):
        assert exact_match("Hello", "hello")

    def test_exact_match_false(self):
        assert not exact_match("hello", "world")

    def test_semantic_similarity_identical(self):
        assert semantic_similarity("test", "test") == 1.0

    def test_semantic_similarity_different(self):
        assert 0 <= semantic_similarity("abc", "xyz") < 0.5

    def test_compute_metrics_returns_all(self):
        metrics = compute_metrics("hello world", ["hello world", "hi world"])
        assert "rouge_l" in metrics
        assert "bleu_1" in metrics
        assert "exact_match" in metrics
        assert "semantic_sim" in metrics
        assert metrics["rouge_l"] == 1.0
        assert metrics["exact_match"] is True


class TestBenchmarks:
    def test_benchmarks_list_not_empty(self):
        assert len(BENCHMARK_TASKS) > 0

    def test_each_task_has_name(self):
        for task in BENCHMARK_TASKS:
            assert "name" in task
            assert "category" in task
            assert "prompt" in task
            assert "expected" in task

    def test_get_by_category(self):
        math_tasks = get_benchmarks_by_category("math")
        assert len(math_tasks) > 0
        for t in math_tasks:
            assert t["category"] == "math"

    def test_get_all_categories(self):
        cats = get_all_categories()
        assert "math" in cats
        assert "code" in cats
        assert isinstance(cats, list)

    def test_categories_unique(self):
        cats = get_all_categories()
        assert len(cats) == len(set(cats))
