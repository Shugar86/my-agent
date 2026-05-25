"""Quality metrics for LLM outputs."""
import re
from typing import List, Dict
from difflib import SequenceMatcher


def rouge_l(hypothesis: str, reference: str) -> float:
    """ROUGE-L F1 score based on longest common subsequence."""
    hyp_tokens = hypothesis.split()
    ref_tokens = reference.split()
    if not hyp_tokens or not ref_tokens:
        return 0.0

    lcs_len = _lcs_length(hyp_tokens, ref_tokens)
    if lcs_len == 0:
        return 0.0

    precision = lcs_len / len(hyp_tokens)
    recall = lcs_len / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _lcs_length(a: List[str], b: List[str]) -> int:
    """Dynamic programming LCS length."""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def bleu_1(hypothesis: str, references: List[str]) -> float:
    """Simplified BLEU-1 (unigram precision with brevity penalty)."""
    hyp_tokens = hypothesis.split()
    if not hyp_tokens:
        return 0.0

    max_ref_len = max(len(r.split()) for r in references) if references else 0
    bp = 1.0 if len(hyp_tokens) >= max_ref_len else (len(hyp_tokens) / max_ref_len) if max_ref_len else 0.0

    matches = 0
    for ref in references:
        ref_tokens = ref.split()
        matches += sum(1 for t in hyp_tokens if t in ref_tokens)
    precision = matches / (len(hyp_tokens) * len(references)) if references else 0
    return bp * precision


def exact_match(hypothesis: str, reference: str) -> bool:
    """Exact string match after normalization."""
    return _normalize(hypothesis) == _normalize(reference)


def f1_score(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def semantic_similarity(a: str, b: str) -> float:
    """Simple sequence matcher similarity (0-1)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text


def compute_metrics(hypothesis: str, references: List[str]) -> Dict[str, float]:
    """Compute all available metrics."""
    return {
        "rouge_l": max(rouge_l(hypothesis, ref) for ref in references),
        "bleu_1": bleu_1(hypothesis, references),
        "exact_match": any(exact_match(hypothesis, ref) for ref in references),
        "semantic_sim": max(semantic_similarity(hypothesis, ref) for ref in references),
    }
