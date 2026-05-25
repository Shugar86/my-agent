"""Standalone script to test real local LLM via Ollama.
Usage: python scripts/test_ollama_real.py
"""
import asyncio
import time
import sys
import httpx

OLLAMA_URL = "http://localhost:11434"
MODEL = "gemma4:e2b"


async def generate(prompt: str, system: str = "") -> tuple:
    t0 = time.time()
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.7},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
    latency = (time.time() - t0) * 1000
    return data.get("response", ""), latency, data.get("eval_count", 0)


async def chat(messages: list) -> tuple:
    t0 = time.time()
    payload = {"model": MODEL, "messages": messages, "stream": False, "options": {"temperature": 0.7}}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
    latency = (time.time() - t0) * 1000
    return data.get("message", {}).get("content", ""), latency, data.get("eval_count", 0)


async def main():
    print("=" * 60)
    print("REAL LOCAL LLM TEST (Ollama + gemma4:e2b)")
    print("=" * 60)

    # Check connectivity
    print("\n[Check] Ollama connectivity...")
    async with httpx.AsyncClient(timeout=5) as c:
        r = await c.get(f"{OLLAMA_URL}/api/tags")
    models = [m["name"] for m in r.json().get("models", [])]
    print(f"  Available models: {models}")
    assert MODEL in models, f"Model {MODEL} not in {models}"

    results = []

    # Test 1: Simple QA
    print("\n[Test 1] Simple QA...")
    ans, lat, tok = await generate("Capital of France? One word.", "Be concise.")
    ok = "paris" in ans.lower()
    results.append(("Simple QA", ok, lat, tok, ans.strip()))
    print(f"  {'PASS' if ok else 'FAIL'} | {lat:.0f}ms | {tok} tokens | {ans.strip()[:50]}")

    # Test 2: Math
    print("\n[Test 2] Math...")
    ans, lat, tok = await generate("15 * 23 + 7 = ? Only number.", "Calculator mode.")
    ok = "352" in ans
    results.append(("Math", ok, lat, tok, ans.strip()))
    print(f"  {'PASS' if ok else 'FAIL'} | {lat:.0f}ms | {tok} tokens | {ans.strip()[:50]}")

    # Test 3: Code
    print("\n[Test 3] Code...")
    ans, lat, tok = await generate("Write a python program to print hello world.", "")
    ok = len(ans.strip()) > 0
    results.append(("Code", ok, lat, tok, ans.strip()))
    print(f"  {'PASS' if ok else 'FAIL'} | {lat:.0f}ms | {tok} tokens | {ans.strip()[:60]}")

    # Test 4: Russian
    print("\n[Test 4] Russian...")
    ans, lat, tok = await generate("Привет! Ответь коротко по-русски.", "")
    has_ru = any(ord(c) > 127 for c in ans)
    ok = has_ru
    results.append(("Russian", ok, lat, tok, ans.strip()))
    print(f"  {'PASS' if ok else 'FAIL'} | {lat:.0f}ms | {tok} tokens | {ans.strip()[:80]}")

    # Test 5: Multi-turn context
    print("\n[Test 5] Multi-turn...")
    ans, lat, tok = await chat([
        {"role": "user", "content": "My name is Alice. Remember it."},
        {"role": "assistant", "content": "Hello Alice, nice to meet you!"},
        {"role": "user", "content": "What is my name?"},
    ])
    ok = "Alice" in ans or "alice" in ans.lower()
    results.append(("Multi-turn", ok, lat, tok, ans.strip()))
    print(f"  {'PASS' if ok else 'FAIL'} | {lat:.0f}ms | {tok} tokens | {ans.strip()[:60]}")

    # Test 6: Tool awareness
    print("\n[Test 6] Tool awareness...")
    ans, lat, tok = await generate("Calculate 2^10. You can use Python code.", "")
    ok = any(x in ans.lower() for x in ["1024", "python", "code"])
    results.append(("Tool aware", ok, lat, tok, ans.strip()))
    print(f"  {'PASS' if ok else 'FAIL'} | {lat:.0f}ms | {tok} tokens | {ans.strip()[:60]}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok, _, _, _ in results if ok)
    total = len(results)
    total_time = sum(lat for _, _, lat, _, _ in results)
    total_tokens = sum(tok for _, _, _, tok, _ in results)

    for name, ok, lat, tok, _ in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {lat:.0f}ms ({tok} eval tokens)")

    print(f"\nTotal: {passed}/{total} passed")
    print(f"Total inference time: {total_time:.0f}ms ({total_time/1000:.1f}s)")
    print(f"Total eval tokens: {total_tokens}")
    print(f"UX Score: {passed/total*100:.0f}%")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
