"""AI Evaluation framework."""
from core.eval.prompt_eval import PromptEvaluator, PromptVariant, EvalResult
from core.eval.quality_metrics import (
    rouge_l, bleu_1, exact_match, semantic_similarity, compute_metrics, f1_score
)
from core.eval.benchmarks import BENCHMARK_TASKS, get_benchmarks_by_category, get_all_categories

__all__ = [
    "PromptEvaluator",
    "PromptVariant",
    "EvalResult",
    "rouge_l",
    "bleu_1",
    "exact_match",
    "semantic_similarity",
    "compute_metrics",
    "f1_score",
    "BENCHMARK_TASKS",
    "get_benchmarks_by_category",
    "get_all_categories",
]
