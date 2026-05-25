import asyncio
import httpx

async def gen(prompt, num_predict=400):
    payload = {
        "model": "gemma4:e2b",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": num_predict},
    }
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post("http://localhost:11434/api/generate", json=payload)
        data = r.json()
    return data.get("response", "")

async def main():
    print("=" * 60)
    print("ТЕСТ gemma4:e2b на генерацию русского текста")
    print("=" * 60)

    prompts = [
        "Напиши краткое введение для научного доклада про аддитивные технологии (3D-печать) в России. 2-3 предложения.",
        "Перечисли 3 российские компании в сфере 3D-печати: НПО СПЛИТ, Росатом, Формотрафик. 1 предложение.",
        "Напиши абзац про перспективы 3D-печати в России до 2030 года. 2 предложения.",
    ]

    for i, p in enumerate(prompts, 1):
        print(f"\n[Test {i}] {p[:50]}...")
        try:
            ans = await gen(p, num_predict=300)
            print(f"  Ответ: {ans[:200]}")
            print(f"  Длина: {len(ans)} символов")
        except Exception as e:
            print(f"  ОШИБКА: {e}")

if __name__ == "__main__":
    asyncio.run(main())
