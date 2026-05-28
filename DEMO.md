# My Agent — Demo Guide

> **TL;DR.** My Agent — AI Agent OS. Опишите задачу — получите
> AI-оператора для бизнеса. Без кода, без интегратора, за 2 минуты.
>
> Позиционирование: **n8n + CrewAI + marketplace в одном продукте,
> но для бизнес-пользователей, не разработчиков.**
>
> У нас 7 live deployments: ювелирный ритейл, travel, legal SaaS, health content.

---

## Запуск

```bash
cp .env.example .env
# Заполнить OPENROUTER_API_KEY для live agent preview
# AGENT_PASSWORD >= 12 символов для production

docker compose up -d --build
# Open http://localhost:8020/
```

Demo работает **без API-ключей** — public agent preview показывает mock fallback.
С `OPENROUTER_API_KEY` — live AI генерация в реальном времени.

---

## Три killer-фичи

### 1. Agent Preview (лендинг, без регистрации)

**URL:** `http://localhost:8020/` → hero widget или `http://localhost:8020/demo`

Пользователь описывает задачу → AI (deepseek via OpenRouter) генерирует:
- Имя, роль и навыки AI-оператора
- Пример ответа в persona
- Follow-up: можно задать вопрос как клиент

Rate limit: 5 preview / 10 chat req в час на IP.

### 2. Showcase — 7 live кейсов

**URL:** `http://localhost:8020/showcase`

7 вертикальных кейсов с persona snippets:
- Mary Jewelry — Telegram-консультант ювелирного бутика
- PEGAS Touristik — AI-автоканал, 88 cron triggers
- DocBrain — legal SaaS (US/EU), Stripe, $4.99
- Pretenzia — 15 000+ юридических документов
- Центр ЗДОРОВОЙ СТОПЫ — VK health content
- Kormoved — AI-продавец в чатах (lab)
- My Agent — Competitor Intelligence workflow

### 3. Live Chat (после login)

**URL:** `http://localhost:8020/app/chat`

Multi-thread SSE chat с 10 агентами. Поддержка tool calls, web search,
code execution. Session persistence (PG + SQLite unified storage).

---

## 3-минутный script для инвестора

| Время | Действие | Что видит инвестор |
|-------|----------|-------------------|
| 0:00 | Открыть `localhost:8020/` | Hero: «AI-оператор для бизнеса за 2 минуты» + live widget |
| 0:15 | Ввести: «AI-консультант для салона красоты» | Widget генерирует оператора — имя, роль, skills, пример ответа (~10 сек) |
| 0:30 | Задать вопрос: «Сколько стоит маникюр?» | Live ответ в persona (~5 сек) |
| 1:00 | Scroll → showcase cards | 3 live кейса: Mary Jewelry, PEGAS, DocBrain с persona snippets |
| 1:30 | Click → «Все 7 кейсов» → `/showcase` | Полная страница с 7 вертикалями |
| 2:00 | Login → Dashboard | «Создайте AI-оператора для бизнеса» + «Открыть чат» |
| 2:30 | `/app/chat` → напишите промпт | Live response от Universal Agent через OpenRouter |
| 3:00 | Wrap | Marketplace 50+ шаблонов, 30+ skills, 7 live deployments |

### Talking points

- **Рынок:** workflow automation $19B+, AI agents $5B→$200B (Gartner)
- **Конкуренты:** n8n/Zapier = для разработчиков; CrewAI = framework без UI; GPTs = single-shot
- **Мы:** no-code agent creation + marketplace + visual builder для бизнес-пользователей
- **Wedge:** 7 live deployments в RU-рынке (Telegram-first), от $190 до $4.99 за документ

---

## In-app demo (advanced, после login)

`/app/demo` — competitor/beauty/lead preset'ы с optional real run (workflow stepper).
Работает через `PlaygroundDemo` + `demo_router.py`. Mock fallback без ключей.

---

## Troubleshooting

- **Agent preview не работает** → проверить `OPENROUTER_API_KEY` в `.env`; без него — 503
- **No templates in marketplace** → `docker compose exec agent python scripts/seed_workflow_templates.py`
- **Chat пустой после reload** → SSE persistence починен в v4.0; проверить что свежий build
- **Login не работает** → `AGENT_PASSWORD` >= 12 символов при `ENV=production`
