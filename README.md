# My Agent

**AI Agent OS** — опишите задачу, получите AI-оператора для бизнеса. Без кода, без интегратора.

| | |
|---|---|
| **Версия** | 4.0.0 |
| **Стек** | Python 3.11 · FastAPI · React 18 · PostgreSQL · Redis |
| **LLM** | OpenRouter (deepseek, owl-alpha, claude и др.) |
| **Документация** | [docs/README.md](docs/README.md) — полный индекс |

---

## Быстрый старт (Docker)

```bash
cp .env.example .env
# Минимум: OPENROUTER_API_KEY (public demo работает и без ключей — mock fallback)
# AGENT_PASSWORD — в production >= 12 символов

docker compose up -d --build
```

| URL | Назначение |
|-----|------------|
| http://localhost:8020/ | Лендинг — live demo «Создайте AI-оператора» |
| http://localhost:8020/showcase | 7 вертикальных кейсов в production |
| http://localhost:8020/demo | Live agent preview (shortcut) |
| http://localhost:8020/app/ | Продукт (после login) |
| http://localhost:8020/login | JWT + Google OAuth |

Логин по умолчанию: `admin` / значение `AGENT_PASSWORD` из `.env`. В **production** (`ENV=production`) пароль должен быть >= 12 символов.

---

## Что умеет My Agent

- **Agent Preview** — опишите задачу текстом → AI генерирует оператора (live LLM, без регистрации)
- **10 агентов** — universal, researcher, developer, marketer, data_analyst, slides, docs, media, data_engineer, news
- **30+ skills** — research, browser, RAG, docs/slides, messaging, scheduler, code execution, OCR, vision и др.
- **AutoAgentFactory** — LLM анализирует задачу, создаёт sub-агентов, запускает параллельно
- **Workflow engine** — visual DAG builder (React Flow), 21+ типов узлов, async runs, Redis queue
- **Marketplace** — 50+ шаблонов, install в один клик, публичный share
- **7 live deployments** — Mary Jewelry, PEGAS Touristik, DocBrain, Pretenzia и др.
- **Интеграции** — Telegram, Slack, n8n webhook, Google OAuth, Gmail, Sheets

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Структура репозитория

```
my-agent/
├── agent.py              # CLI
├── web/
│   ├── server.py         # FastAPI
│   ├── demo_router.py    # Public agent preview + demo endpoints
│   └── frontend/         # React SPA (Vite, bun)
├── core/                 # runtime, orchestrator, workflow, auth
├── skills/               # доменные навыки (SKILL.md + skill.py)
├── tools/                # регистрация инструментов
├── agents/registry.json  # профили агентов (model: "balanced" → OpenRouter)
├── config/               # agent.json, models.yaml
├── tests/                # pytest (+ Playwright e2e)
├── deploy/               # prod compose, monitoring
└── docker-compose.yml    # db + redis + agent (:8020)
```

---

## Локальная разработка

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env     # заполнить OPENROUTER_API_KEY

# PostgreSQL + Redis (или docker compose up db redis -d)
export DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
export REDIS_URL=redis://127.0.0.1:6380/0

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

### Frontend

```bash
cd web/frontend && bun install && bun run build
# Dev: bun run dev (proxy на :8020)
```

### Тесты

```bash
pytest tests/test_code_tools.py tests/test_file_tools.py \
       tests/test_security_improvements.py tests/test_async_utils.py \
       tests/test_db_manager.py tests/test_production_hardening.py \
       tests/test_all.py::test_memory_manager -q

bash scripts/check-secrets.sh
python -m pytest tests/test_demo_flow.py tests/test_marketplace.py -q
```

---

## Web UI — маршруты

| Маршрут | Описание |
|---------|----------|
| `/` | Лендинг: hero + agent preview + showcase cards + marketplace |
| `/showcase` | 7 vertical кейсов + agent preview widget |
| `/demo` | Live agent preview (shortcut) |
| `/login` | Вход / регистрация |
| `/app/` | Dashboard: chat-first hero + showcase + templates |
| `/app/chat` | Multi-thread chat с агентами (SSE) |
| `/app/workflows`, `/app/workflows/:id` | Список и visual builder |
| `/app/marketplace` | Шаблоны |
| `/app/settings` | API keys, agents, integrations, MCP |
| `/app/onboarding` | 4-step wizard (agent preview → usecase → workspace → integrations) |
| `/app/demo` | In-app competitor demo (PlaygroundDemo, behind login) |

---

## Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `OPENROUTER_API_KEY` | Primary LLM (все агенты через profile `balanced`) |
| `NEUROAPI_API_KEY` | Альтернативный LLM provider |
| `TAVILY_API_KEY` | Веб-поиск для research workflows |
| `DATABASE_URL` | PostgreSQL (обязателен в production) |
| `REDIS_URL` | Кэш, rate limits, workflow queue |
| `AGENT_PASSWORD` | Пароль admin (prod: >= 12 символов) |
| `AGENT_SECRET_KEY` | JWT secret (>= 32 символа) |
| `CORS_ORIGINS` | Доп. origins через запятую |

Полный список: [.env.example](.env.example).

---

## Связанные документы

| Тема | Файл |
|------|------|
| Демо инвесторам | [DEMO.md](DEMO.md) |
| Деплой | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Безопасность | [SECURITY.md](SECURITY.md) |
| Изменения | [CHANGELOG.md](CHANGELOG.md) |
| Аудит / проблемы | [TROUBLES.md](TROUBLES.md) |

**Лицензия:** MIT
