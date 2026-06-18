# My Agent — Investor Quick Reference

One-page cheat sheet for demos and pitch meetings.

## URLs

| Surface | URL | Notes |
|---------|-----|-------|
| **Лендинг + live demo** | **`/`** | Hero: agent preview widget (live AI, без login) |
| 7 кейсов в production | `/showcase` | Vertical cards + agent preview |
| Demo shortcut | `/demo` | Agent preview (вторичный вход) |
| Login | `/login` | JWT + Google OAuth |
| Продукт | `/app` | Dashboard: chat-first hero |
| Chat | `/app/chat` | Multi-thread SSE с 10 агентами |
| Marketplace | `/app/marketplace` | 50+ шаблонов |

## Env flags

| Variable | Purpose |
|----------|---------|
| `OPENROUTER_API_KEY` | LLM для agent preview + chat + real demo runs |
| `TAVILY_API_KEY` | Web search для research workflows (optional) |
| `AGENT_PASSWORD` | Admin password (>= 12 chars in production) |

Public demo работает без ключей — mock fallback.
С ключом — live AI agent preview на лендинге.

## 3-minute script

1. Открыть **`/`** → hero widget → ввести задачу → live agent preview (~10 сек)
2. Задать вопрос оператору → live ответ в persona
3. Scroll → 3 showcase cards (Mary Jewelry, PEGAS, DocBrain)
4. Login → `/app/chat` → live multi-turn chat
5. Wrap → marketplace 50+ шаблонов, 7 live deployments

## Showcase verticals (7 cards)

| # | Vertical | Status | Proof |
|---|----------|--------|-------|
| 1 | Mary Jewelry — Telegram-консультант | Production | 4 persona, RAG |
| 2 | PEGAS Touristik — автоканал | Production | 88 cron triggers |
| 3 | Центр ЗДОРОВОЙ СТОПЫ — VK health | Production | 75 daily triggers |
| 4 | DocBrain — legal SaaS (US/EU) | Production | Stripe, $4.99 |
| 5 | Pretenzia — претензии РФ | Production | 15 000+ docs |
| 6 | Kormoved — AI-продавец | Lab | anti-detect, funnel |
| 7 | My Agent — Competitor Intelligence | Production | DAG workflow |

## Key metrics

- 50+ marketplace шаблонов
- 10 агентов, 33 skills, 80+ tools
- 7 live deployments
- AutoAgentFactory: LLM → sub-agents → parallel execution → synthesis
