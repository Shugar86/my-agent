"""Standalone script to run real API UX tests.
Usage: python scripts/test_api_ux.py
"""
import asyncio
import time
import sys
import os

# Force UTF-8 for Windows
os.environ["PYTHONIOENCODING"] = "utf-8"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import litellm

MODEL = "openrouter/deepseek/deepseek-v4-flash:free"
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
BASE_URL = "https://openrouter.ai/api/v1"


async def call_llm(messages, timeout=30):
    start = time.time()
    try:
        resp = await litellm.acompletion(
            model=MODEL,
            messages=messages,
            api_key=API_KEY,
            api_base=BASE_URL,
            timeout=timeout,
        )
        latency = (time.time() - start) * 1000
        tokens = resp.usage.total_tokens if resp.usage else 0
        return resp.choices[0].message.content, latency, tokens, None
    except Exception as e:
        return None, (time.time() - start) * 1000, 0, str(e)


async def main():
    print("=" * 60)
    print("REAL API UX / PERFORMANCE TEST")
    print(f"Model: {MODEL}")
    print("=" * 60)

    results = []

    # Test 1: Ping (cold-start)
    print("\n[Test 1] API Ping (cold-start)...")
    answer, latency, tokens, err = await call_llm([
        {"role": "user", "content": "Say 'pong' and nothing else."}
    ])
    if err:
        print(f"  ERROR: {err[:200]}")
        results.append(("API Ping", False, latency, tokens, err[:50]))
    else:
        ok = "pong" in answer.lower()
        results.append(("API Ping", ok, latency, tokens, answer[:50]))
        print(f"  Result: {'PASS' if ok else 'FAIL'} | {latency:.0f}ms | {tokens} tokens")
        print(f"  Answer: {answer[:60]}")

    # Test 2: Simple QA
    print("\n[Test 2] Simple QA...")
    answer, latency, tokens, err = await call_llm([
        {"role": "system", "content": "Be concise. 1 sentence."},
        {"role": "user", "content": "Capital of France?"},
    ])
    if err:
        print(f"  ERROR: {err[:200]}")
        results.append(("Simple QA", False, latency, tokens, err[:50]))
    else:
        ok = "Paris" in answer
        results.append(("Simple QA", ok, latency, tokens, answer[:50]))
        print(f"  Result: {'PASS' if ok else 'FAIL'} | {latency:.0f}ms | {tokens} tokens")
        print(f"  Answer: {answer[:60]}")

    # Test 3: Tool reasoning
    print("\n[Test 3] Tool reasoning...")
    answer, latency, tokens, err = await call_llm([
        {"role": "system", "content": "You can run Python code. Mention this if user asks math."},
        {"role": "user", "content": "Calculate 15*23+7"},
    ])
    if err:
        print(f"  ERROR: {err[:200]}")
        results.append(("Tool Reasoning", False, latency, tokens, err[:50]))
    else:
        ok = any(x in answer.lower() for x in ["352", "python", "code", "calculate"])
        results.append(("Tool Reasoning", ok, latency, tokens, answer[:50]))
        print(f"  Result: {'PASS' if ok else 'FAIL'} | {latency:.0f}ms | {tokens} tokens")
        print(f"  Answer: {answer[:80]}")

    # Test 4: Code generation
    print("\n[Test 4] Code generation...")
    answer, latency, tokens, err = await call_llm([
        {"role": "system", "content": "Respond with code only, no explanation."},
        {"role": "user", "content": "Python one-liner reverse [1,2,3]"},
    ])
    if err:
        print(f"  ERROR: {err[:200]}")
        results.append(("Code Gen", False, latency, tokens, err[:50]))
    else:
        ok = "[::-1]" in answer or "reversed" in answer.lower()
        results.append(("Code Gen", ok, latency, tokens, answer[:50]))
        print(f"  Result: {'PASS' if ok else 'FAIL'} | {latency:.0f}ms | {tokens} tokens")
        print(f"  Answer: {answer[:60]}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, ok, _, _, _ in results if ok)
    total = len(results)
    total_tokens = sum(tokens for _, _, _, tokens, _ in results)
    total_time = sum(lat for _, _, lat, _, _ in results)

    for name, ok, lat, tok, _ in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}: {lat:.0f}ms ({tok} tokens)")

    print(f"\nTotal: {passed}/{total} passed")
    print(f"Total tokens used: {total_tokens}")
    print(f"Total API time: {total_time:.0f}ms ({total_time/1000:.1f}s)")
    print(f"UX Score: {passed/total*100:.0f}%")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
