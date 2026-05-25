"""A/B prompt evaluation framework."""
import asyncio
import json
import time
from typing import List, Dict, Any, Callable
from dataclasses import dataclass

from core.llm_gateway import LLMGateway


@dataclass
class PromptVariant:
    name: str
    system_prompt: str
    user_prompt: str
    params: Dict[str, Any]


@dataclass
class EvalResult:
    variant: str
    response: str
    latency_ms: float
    tokens_used: int
    score: float = 0.0


class PromptEvaluator:
    """Evaluate multiple prompt variants against a judge model."""

    def __init__(self, judge_config: Dict[str, Any]):
        self.judge = LLMGateway(judge_config)

    async def evaluate(
        self,
        variants: List[PromptVariant],
        judge_criteria: str = "Rate the response quality from 0 to 10 based on accuracy, clarity, and helpfulness.",
    ) -> List[EvalResult]:
        """Run all variants and score them with LLM-as-judge."""
        results = []
        for variant in variants:
            start = time.time()
            messages = [
                {"role": "system", "content": variant.system_prompt},
                {"role": "user", "content": variant.user_prompt},
            ]
            response = await self.judge.chat(messages, **variant.params)
            latency = (time.time() - start) * 1000

            # Judge scoring
            judge_prompt = f"{judge_criteria}\n\nResponse to evaluate:\n{response.content}\n\nScore (0-10):"
            judge_messages = [{"role": "user", "content": judge_prompt}]
            judge_resp = await self.judge.chat(judge_messages)
            score_text = judge_resp.content.strip()
            try:
                digits = ''.join([c for c in score_text if c.isdigit() or c == '.'])
                score = float(digits) if digits else 0.0
            except (IndexError, ValueError):
                score = 0.0

            results.append(EvalResult(
                variant=variant.name,
                response=response.content,
                latency_ms=latency,
                tokens_used=len(response.content.split()),
                score=min(score, 10.0),
            ))
        return results

    async def run_benchmark(
        self,
        benchmark_tasks: List[Dict[str, Any]],
        variant_factory: Callable[[Dict], List[PromptVariant]],
    ) -> Dict[str, Any]:
        """Run benchmark suite across multiple tasks."""
        all_results = []
        for task in benchmark_tasks:
            variants = variant_factory(task)
            task_results = await self.evaluate(variants)
            all_results.append({
                "task": task["name"],
                "results": [
                    {
                        "variant": r.variant,
                        "score": r.score,
                        "latency_ms": r.latency_ms,
                        "tokens": r.tokens_used,
                    }
                    for r in task_results
                ],
            })

        # Aggregate
        variant_scores: Dict[str, List[float]] = {}
        for task_res in all_results:
            for r in task_res["results"]:
                variant_scores.setdefault(r["variant"], []).append(r["score"])

        summary = {
            "tasks": len(benchmark_tasks),
            "variants": {
                v: {"avg_score": sum(s) / len(s), "runs": len(s)}
                for v, s in variant_scores.items()
            },
            "winner": max(variant_scores, key=lambda v: sum(variant_scores[v]) / len(variant_scores[v])),
        }
        return {"summary": summary, "details": all_results}
