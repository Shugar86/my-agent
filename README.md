# My Agent

> **AI Agent OS для бизнеса.** Опишите задачу текстом — получите работающего AI-оператора. Без кода, без интегратора, без ожидания.

```text
   __  ___      ____        __              __
  /  |/  /___ _/ __ \____ _/ /___  ______ _/ /_
 / /|_/ / __ `/ / / / __ `/ __/ / / / __ `/ __/
/ /  / / /_/ / /_/ / /_/ / /_/ /_/ / /_/ / /_
/_/  /_/\__, /_____/\__,_/\__/\__,_/\__,_/\__/
       /____/
```

<!-- badge-линия -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](./pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a2a2.svg)](./pyproject.toml)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](./web/frontend)
[![Tests](https://img.shields.io/badge/tests-pytest%20%7C%20playwright-success.svg)](./tests)
[![Docker](https://img.shields.io/badge/docker-compose-2496ed.svg)](./docker-compose.yml)

---

## 📸 Как это выглядит

<p align="center">
  <img src="website/assets/product-dashboard.webp" alt="My Agent — панель: workflows, агенты, маркетплейс, стоимость и токены" width="820">
</p>

<p align="center"><em>Панель: запусти готовый workflow, собери агента, следи за стоимостью прогонов и токенами.</em></p>

> 🔗 **Живое демо** «Опиши задачу → получи AI-оператора» — на лендинге. Подними локально (см. [Быстрый старт](#быстрый-старт)) и открой <http://localhost:8020/>.

---

## Что это

**My Agent** — операционная система для бизнес-агентов. Вы описываете рутинную задачу своими словами, а платформа собирает из неё готового оператора: роль, навыки, память, интеграции и workflow.

Это не очередной чат-бот. Это промежуток между no-code автоматизацией вроде n8n и дорогими AI-студиями: быстрый time-to-wow, живой demo прямо на лендинге и полноценный продукт после входа.

**Для кого:**

- **Малый и средний бизнес**, который хочет автоматизировать research, отчёты, lead-qualification и коммуникации.
- **Команды аналитиков и маркетологов**, уставшие собирать briefы вручную.
- **Продуктовые команды**, которым нужен настраиваемый AI-оператор под собственные процессы.

---

## Возможности

- ✨ **Agent Preview** — опишите задачу текстом, и LLM сгенерирует персону оператора без регистрации.
- 🤖 **10 готовых агентов** — universal, researcher, developer, marketer, data_analyst, slides, docs, media, data_engineer, news.
- 🧰 **30+ навыков** — research, browser, RAG, документы, презентации, планировщик, выполнение кода, OCR, vision, email, RSS и другие.
- ⚡ **AutoAgentFactory** — LLM анализирует задачу, создаёт sub-агентов и запускает их параллельно.
- 🕸️ **Workflow engine** — визуальный DAG-редактор (React Flow), 21+ типов узлов, async-запуски, Redis-очередь.
- 🛒 **Marketplace** — 50+ шаблонов, установка в один клик, публичный share.
- 🚀 **Live deployments** — Mary Jewelry, PEGAS Touristik, DocBrain, Pretenzia и другие кейсы.
- 🔌 **Интеграции** — Telegram, Slack, n8n webhook, Google OAuth, Gmail, Sheets.

Подробнее об архитектуре: [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## Быстрый старт

### Docker (рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone git@github.com:Shugar86/my-agent.git
cd my-agent

# 2. Подготовить окружение
cp .env.example .env
# Минимум: OPENROUTER_API_KEY (public demo работает и без ключей — mock fallback)
# AGENT_PASSWORD — в production >= 12 символов

# 3. Запустить стек
docker compose up -d --build
```

| URL | Назначение |
|-----|------------|
| http://localhost:8020/ | Лендинг — live demo «Создайте AI-оператора» |
| http://localhost:8020/showcase | 7 вертикальных кейсов в production |
| http://localhost:8020/demo | Live agent preview (shortcut) |
| http://localhost:8020/app/ | Продукт (после login) |
| http://localhost:8020/login | JWT + Google OAuth |

Логин по умолчанию: `admin` / значение `AGENT_PASSWORD` из `.env`. В **production** (`ENV=production`) пароль должен быть ≥ 12 символов.

Проверка здоровья:

```bash
curl -s http://localhost:8020/api/health
```

### Локальная разработка

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env     # заполнить OPENROUTER_API_KEY

# PostgreSQL + Redis (или docker compose up db redis -d)
export DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
export REDIS_URL=redis://127.0.0.1:6380/0

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

Frontend:

```bash
cd web/frontend && bun install && bun run build
# Dev: bun run dev (proxy на :8020)
```

---

## Архитектура / стек

| Слой | Технологии |
|------|------------|
| Backend | Python 3.11+, FastAPI, Pydantic 2, SQLAlchemy, asyncpg, Alembic |
| Frontend | React 18, Vite, bun → `web/static/app/` |
| LLM | OpenRouter (litellm), fallback по free-моделям |
| Data | PostgreSQL 16, Redis 7, ChromaDB (RAG) |
| Infra | Docker, docker-compose, Caddyfile |
| Тесты | pytest, Playwright e2e, `scripts/check-secrets.sh` |

### Ключевые компоненты

```text
CLI / Web → FastAPI → Orchestrator → AgentBuilder → AgentRuntime → skills/tools
                              ↓
                    Workflow Engine (DAG + Redis queue)
                              ↓
              PostgreSQL + Redis + ChromaDB
```

---

## Структура репозитория

```text
my-agent/
├── agent.py              # CLI-интерфейс
├── web/
│   ├── server.py         # FastAPI-приложение
│   ├── demo_router.py    # Public agent preview + demo endpoints
│   └── frontend/         # React SPA (Vite, bun)
├── core/                 # runtime, orchestrator, workflow, auth
├── skills/               # доменные навыки (SKILL.md + skill.py)
├── tools/                # регистрация инструментов
├── agents/registry.json  # профили агентов
├── config/               # agent.json, models.yaml
├── tests/                # pytest (+ Playwright e2e)
├── deploy/               # prod compose, monitoring
└── docker-compose.yml    # db + redis + agent (:8020)
```

---

## Примеры

### Сгенерировать агента из описания

```bash
curl -X POST http://localhost:8020/api/demo/public/agent-preview \
  -H "Content-Type: application/json" \
  -d '{"task": "Собирай конкурентный анализ по косметике раз в неделю и присылай PDF"}'
```

### Запустить workflow из marketplace

```bash
curl -X POST http://localhost:8020/api/workflow-templates/tpl_competitor_watch/demo-run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"inputs": {"company": "Acme Inc"}}'
```

### CLI

```bash
python agent.py --help
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
| `/app/onboarding` | 4-step wizard |
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
| `AGENT_PASSWORD` | Пароль admin (prod: ≥ 12 символов) |
| `AGENT_SECRET_KEY` | JWT secret (≥ 32 символа) |
| `CORS_ORIGINS` | Доп. origins через запятую |

Полный список: [.env.example](./.env.example).

---

## Тесты

```bash
# Core security + smoke tests
pytest tests/test_code_tools.py tests/test_file_tools.py \
       tests/test_security_improvements.py tests/test_async_utils.py \
       tests/test_db_manager.py tests/test_production_hardening.py \
       tests/test_all.py::test_memory_manager -q

# Проверка на утечку секретов
bash scripts/check-secrets.sh

# Demo + marketplace
pytest tests/test_demo_flow.py tests/test_marketplace.py -q
```

---

## Характер проекта

**Вайб:** `pragmatic` — «не очередной чат-бот, а работающий оператор».

1. **Time-to-wow.** Живой preview прямо на лендинге: задача текстом → персона оператора без регистрации.
2. **Между no-code и AI-студией.** Проще n8n на старте, серьёзнее чата после входа — без лишней церемонии.
3. **Продукт, а не демо.** Что в production — показано в showcase; секреты и пароли — мимо git.

---

## Участие

PR и идеи приветствуются. Сначала загляните в [CONTRIBUTING.md](./CONTRIBUTING.md) и [AGENTS.md](./AGENTS.md) — там правила игры для людей и для AI-агентов.

---

## Связанные документы

| Тема | Файл |
|------|------|
| Полный индекс документации | [docs/README.md](./docs/README.md) |
| Контракт для агентов | [AGENTS.md](./AGENTS.md) |
| Демо инвесторам | [DEMO.md](./DEMO.md) |
| Деплой | [DEPLOYMENT.md](./DEPLOYMENT.md) |
| Безопасность | [SECURITY.md](./SECURITY.md) |
| Архитектура | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Изменения | [CHANGELOG.md](./CHANGELOG.md) |
| Аудит / проблемы | [TROUBLES.md](./TROUBLES.md) |
| Участие | [CONTRIBUTING.md](./CONTRIBUTING.md) |

---

**Лицензия:** [MIT](./LICENSE) © 2026 Shugar86
