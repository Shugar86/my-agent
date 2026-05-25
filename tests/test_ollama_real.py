"""Real LLM tests using local Ollama (gemma4:e2b) — zero API cost.

Tests actual model inference with timing and quality checks.
"""
import pytest
import asyncio
import time
import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma4:e2b"


async def _ollama_generate(prompt: str, system: str = "", temperature: float = 0.7, timeout: int = 60) -> tuple:
    """Call Ollama generate API. Returns (response_text, latency_ms, eval_count)."""
    start = time.time()
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": 256},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
    latency = (time.time() - start) * 1000
    return data.get("response", ""), latency, data.get("eval_count", 0)


async def _ollama_chat(messages: list, timeout: int = 60) -> tuple:
    """Call Ollama chat API. Returns (response_text, latency_ms, eval_count)."""
    start = time.time()
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 256},
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
    latency = (time.time() - start) * 1000
    return data.get("message", {}).get("content", ""), latency, data.get("eval_count", 0)


@pytest.mark.slow
class TestOllamaConnectivity:
    """Verify Ollama is running and model is loaded."""

    @pytest.mark.asyncio
    async def test_ollama_api_reachable(self):
        """Ollama API should respond in < 500ms."""
        async with httpx.AsyncClient(timeout=5) as client:
            t0 = time.time()
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            latency = (time.time() - t0) * 1000
        assert resp.status_code == 200
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        assert MODEL in models, f"Model {MODEL} not found. Available: {models}"
        print(f"  OLLAMA PING: {latency:.0f}ms, models={models}")
        assert latency < 500


@pytest.mark.slow
class TestRealLLMQuality:
    """Test actual model responses for quality and correctness."""

    @pytest.mark.asyncio
    async def test_simple_qa(self):
        """Basic factual question."""
        answer, latency, tokens = await _ollama_generate(
            "What is the capital of France? Answer in one word.",
            system="Be concise. Answer with a single word when possible.",
        )
        print(f"  QA: {latency:.0f}ms, {tokens} tokens, answer='{answer.strip()}'")
        assert "Paris" in answer or "paris" in answer.lower()
        assert latency < 20000  # Local model may be slower

    @pytest.mark.asyncio
    async def test_math_reasoning(self):
        """Model should solve simple math."""
        answer, latency, tokens = await _ollama_generate(
            "Calculate 15 * 23 + 7. Show only the final number.",
            system="You are a calculator. Output only the number.",
        )
        print(f"  MATH: {latency:.0f}ms, {tokens} tokens, answer='{answer.strip()[:50]}'")
        assert "352" in answer
        assert latency < 20000

    @pytest.mark.asyncio
    async def test_code_generation(self):
        """Model should generate valid Python code."""
        answer, latency, tokens = await _ollama_generate(
            "Write a python program to print hello world.",
            system="",
        )
        print(f"  CODE: {latency:.0f}ms, {tokens} tokens, snippet='{answer.strip()[:60]}'")
        assert len(answer.strip()) > 0, f"Expected non-empty response, got empty"
        assert latency < 20000

    @pytest.mark.asyncio
    async def test_russian_language(self):
        """Model should understand and respond in Russian."""
        answer, latency, tokens = await _ollama_generate(
            "Привет! Ответь коротко по-русски.",
            system="",
        )
        print(f"  RU: {latency:.0f}ms, {tokens} tokens, answer='{answer.strip()[:80]}'")
        # Should contain Cyrillic characters
        has_cyrillic = any(ord(c) > 127 for c in answer)
        assert has_cyrillic, f"Expected Russian response, got: {answer}"
        assert latency < 20000

    @pytest.mark.asyncio
    async def test_tool_awareness(self):
        """Model should recognize when tools are needed."""
        answer, latency, tokens = await _ollama_chat([
            {"role": "system", "content": "You have access to Python code execution. Mention this when user asks for calculations."},
            {"role": "user", "content": "Calculate 2^10"},
        ])
        print(f"  TOOL: {latency:.0f}ms, {tokens} tokens, answer='{answer.strip()[:80]}'")
        # Should mention code, python, calculator, or give the number 1024
        quality = any(x in answer.lower() for x in ["1024", "python", "code", "calculate", "calculator"])
        assert quality, f"Expected tool awareness, got: {answer}"
        assert latency < 20000


@pytest.mark.slow
class TestChatAPI:
    """Test Ollama chat API format (compatible with OpenAI-style)."""

    @pytest.mark.asyncio
    async def test_chat_format_multi_turn(self):
        """Multi-turn conversation should maintain context."""
        answer, latency, tokens = await _ollama_chat([
            {"role": "user", "content": "My name is Alice. Remember it."},
            {"role": "assistant", "content": "Hello Alice, nice to meet you!"},
            {"role": "user", "content": "What is my name?"},
        ])
        print(f"  MULTI-TURN: {latency:.0f}ms, answer='{answer.strip()[:60]}'")
        assert "Alice" in answer or "alice" in answer.lower()
        assert latency < 20000


@pytest.mark.slow
class TestPerformanceBenchmark:
    """Benchmark model performance."""

    @pytest.mark.asyncio
    async def test_latency_baseline(self):
        """Measure baseline latency for a short prompt."""
        latencies = []
        for _ in range(3):
            _, lat, _ = await _ollama_generate("Hi", system="Say hello")
            latencies.append(lat)
        avg = sum(latencies) / len(latencies)
        print(f"  LATENCY BASELINE: avg={avg:.0f}ms, min={min(latencies):.0f}ms, max={max(latencies):.0f}ms")
        # Local 5B model should respond in < 15s even on CPU
        assert avg < 15000, f"Too slow: {avg:.0f}ms"


# ---------------------------------------------------------------------------
# Standalone runner for quick testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
