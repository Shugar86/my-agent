# My Agent

**Autonomous Workflow OS** — визуальный конструктор workflow, маркетплейс шаблонов, multi-agent чат и deep research (OpenRouter + 33 skills).

| | |
|---|---|
| **Версия** | 3.5.3 |
| **Стек** | Python 3.11 · FastAPI · React 18 · PostgreSQL · Redis |
| **Документация** | [docs/README.md](docs/README.md) — полный индекс |

---

## Быстрый старт (Docker)

```bash
cp .env.example .env
# Live chat / real demo: OPENROUTER_API_KEY (+ TAVILY_API_KEY для поиска)
# Без ключей публичное demo на mock replay всё равно работает

docker compose up -d --build
# Первый старт: seed шаблонов + demo DOCX (entrypoint)
```

| URL | Назначение |
|-----|------------|
| http://localhost:8020/ | Публичный лендинг (React) |
| **http://localhost:8020/showcase#playground** | **Канонический demo** — Competitor Intelligence 90s → DOCX |
| http://localhost:8020/showcase | 7 вертикальных кейсов + playground |
| http://localhost:8020/demo | Shortcut на тот же playground (вторичный) |
| http://localhost:8020/app/ | Продукт (после login) |
| http://localhost:8020/login | JWT + Google OAuth |

Логин по умолчанию: `admin` / `admin` (сменить `AGENT_PASSWORD` в `.env`).

Демо с n8n: `docker compose --profile demo up -d --build` → [DEMO.md](DEMO.md).

---

## Возможности

- **Workflow engine** — DAG builder (React Flow), 21+ типов узлов, async runs, Redis queue
- **Marketplace** — 52 шаблона, demo-run, публичный share `/app/share/templates/:id`
- **7 агентов** — universal, researcher, developer, marketer, data_analyst, slides, docs
- **33 skills** — research, browser, RAG, docs/slides, messaging, scheduler, …
- **Интеграции** — Telegram, Slack, n8n webhook, Google OAuth
- **Production** — PostgreSQL + Redis обязательны при `ENV=production`; Prometheus/Grafana (`--profile monitoring`)

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Структура репозитория

```
my-agent/
├── agent.py              # CLI
├── web/
│   ├── server.py         # FastAPI
│   └── frontend/         # React SPA (Vite, bun)
├── core/                 # runtime, orchestrator, workflow, auth, billing
├── skills/               # доменные навыки (SKILL.md + skill.py)
├── tools/                # регистрация инструментов
├── agents/registry.json  # профили агентов
├── config/               # agent.json, models.yaml
├── tests/                # pytest (+ Playwright в web/frontend/e2e)
├── deploy/               # prod compose, systemd, monitoring
├── docs/                 # индекс и архив аудитов
└── docker-compose.yml    # db + redis + agent (:8020)
```

---

## Локальная разработка

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

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
python -m pytest tests/test_demo_flow.py tests/test_marketplace.py -q
# E2E canonical demo (нужен сервер на :8020):
cd web/frontend && E2E_DEMO_RUN=1 npx playwright test e2e/investor-funnel.spec.ts -g "Canonical demo"
```

Smoke после деплоя:

```bash
curl -s http://127.0.0.1:8020/api/health
docker compose exec -T agent python -m pytest tests/test_demo_flow.py -q
```

---

## Web UI — маршруты

| Маршрут | Описание |
|---------|----------|
| `/`, `/showcase`, `/demo` | Публичные (без auth); **канонический demo:** `/showcase#playground` |
| `/login` | Вход / регистрация |
| `/app/` | Dashboard, activation hero |
| `/app/chat` | Чат с агентами (live при `OPENROUTER_API_KEY`) |
| `/app/workflows`, `/app/workflows/:id` | Список и builder |
| `/app/marketplace` | Шаблоны |
| `/app/settings` | Интеграции, API keys, billing, agents/knowledge/MCP (tabs) |
| `/app/onboarding` | 4-step wizard |
| `/app/demo`, `/app/showcase` | In-app demo и кейсы |

Редиректы: `/app/agents` → `settings?tab=agents`, `/welcome` → `/`.

Дизайн: [web/frontend/DESIGN.md](web/frontend/DESIGN.md).

---

## Переменные окружения

| Переменная | Назначение |
|------------|------------|
| `OPENROUTER_API_KEY` | Primary LLM (OpenRouter) |
| `TAVILY_API_KEY` | Веб-поиск для live runs (опционально) |
| `KIMI_API_KEY` | Kimi Code API (опционально, если модель в registry — Kimi) |
| `DATABASE_URL` | PostgreSQL (обязателен в production) |
| `REDIS_URL` | Кэш, rate limits, workflow queue |
| `AGENT_PASSWORD` / `AGENT_SECRET_KEY` | Админ и JWT |

Полный список: [.env.example](.env.example).

---

## Связанные документы

| Тема | Файл |
|------|------|
| RU-руководство | [PROJECT_GUIDE.md](PROJECT_GUIDE.md) |
| Handoff / automation | [HANDOFF.md](HANDOFF.md) |
| Деплой | [DEPLOYMENT.md](DEPLOYMENT.md) · [SERVER.md](SERVER.md) |
| Безопасность | [SECURITY.md](SECURITY.md) |
| Демо инвесторам | [DEMO.md](DEMO.md) · [INVESTOR.md](INVESTOR.md) |
| Изменения | [CHANGELOG.md](CHANGELOG.md) |
| Проблемы | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Архив аудитов | [docs/archive/](docs/archive/) |

**Лицензия:** MIT
