# PROJECT — my-agent

Anchor (immutable core). Изменение смысла = новый проект.

## Mission (north star)

**AI Agent OS** — пользователь описывает бизнес-задачу текстом и получает готового AI-оператора без кода и без интегратора. Продукт между no-code автоматизацией (n8n/Zapier) и дорогими AI-студиями: быстрый time-to-wow, живой demo на лендинге, полноценный продукт после входа.

## Immutable core (принципы, которые нельзя ломать)

1. **Задача → оператор** — публичный Agent Preview и продуктовый чат должны превращать описание задачи в работающего агента (persona + skills), а не в пустой CRUD.
2. **Live demo без барьера** — лендинг (`/`, `/demo`, `/showcase`) доступен без регистрации; при отсутствии ключей — предсказуемый mock/fallback, не падение UI.
3. **Один runtime** — CLI (`agent.py`) и Web (`web/server.py`) используют общий стек: Orchestrator → AgentBuilder → AgentRuntime → skills/tools.
4. **Production data** — при `ENV=production` основные данные в PostgreSQL + Redis; SQLite только для dev без production-флага.
5. **Безопасность по умолчанию** — JWT httpOnly, rate limits, sandbox для code exec, fail-closed admin password (≥12 символов), публичные пути явно в `web/security.py`.
6. **Честные статусы** — UI badges (Live / Beta / Preview / Скоро) отражают реальное подключение backend, не маркетинговую фикцию.

## Key technical decisions

| Решение | Почему |
|---------|--------|
| FastAPI + React SPA (Vite, bun) | Единый HTTP/SSE API, современный UI, visual workflow builder (React Flow) |
| OpenRouter как primary LLM | Единый шлюз к free/paid моделям; Kimi выведен из `agents/registry.json` (v4) |
| PostgreSQL + Redis | Пользователи, workflows, billing; очереди, rate limit, session blacklist |
| LiteLLM + `core/configurator.py` | Профили моделей (`balanced`, `fast`) и env-подстановка ключей |
| Workflow engine (DAG + Redis queue) | Async runs, 21+ типов узлов, интеграция n8n webhook |
| ChromaDB | RAG knowledge base для skills |
| Docker Compose (:8020) | Один командный старт: db + redis + agent; порт 8020 — канонический |
| Alembic | Миграции схемы; `DATABASE_URL` в `alembic/env.py` |

## Stack

| Слой | Технологии |
|------|------------|
| Backend | Python 3.11+, FastAPI, uvicorn, Pydantic 2, SQLAlchemy, asyncpg, alembic |
| Frontend | React 18, Vite, bun → `web/static/app/` |
| LLM | OpenRouter (litellm), fallback по free-моделям в demo_router |
| Data | PostgreSQL 16, Redis 7, ChromaDB; JSON sessions в dev |
| Infra | Docker, docker-compose, Caddyfile [deploy], Prometheus metrics |
| Тесты | pytest, Playwright e2e, `scripts/check-secrets.sh` |
| Ключевые Python-libs | litellm, slowapi, python-jose, docker SDK, MCP, APScheduler |

Версия продукта: **4.0.0** (см. [CHANGELOG.md](CHANGELOG.md)).

## Key files / entry points

| Путь | Назначение |
|------|------------|
| `agent.py` | CLI: chat, serve, list-agents, test |
| `web/server.py` | FastAPI app, middleware, роутеры |
| `web/demo_router.py` | Public agent-preview, agent-chat, LLM fallback |
| `core/orchestrator.py` | Multi-agent handoff / parallel delegate |
| `core/auto_agent_factory.py` | LLM → sub-agents → parallel run |
| `core/builder.py`, `core/runtime.py` | Сборка и цикл агента |
| `core/workflow/*` | DAG store, executor, Redis queue |
| `agents/registry.json` | 10 профилей агентов |
| `config/agent.json`, `config/models.yaml` | Конфиг моделей |
| `skills/*/skill.py` | 33 доменных навыка |
| `docker-compose.yml` | Локальный/prod stack |
| `Dockerfile` | Образ agent |
| `.env.example` | Обязательные env-переменные |

## Documentation

| Документ | Содержание |
|----------|------------|
| [README.md](README.md) | Обзор, quick start, маршруты |
| [docs/README.md](docs/README.md) | Полный индекс |
| [AGENTS.md](AGENTS.md) | Контракт для AI-агентов |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Слои, workflow, security |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Деплой |
| [SERVER.md](SERVER.md) | VDS, порты, nginx |
| [SECURITY.md](SECURITY.md) | JWT, checklist |
| [DEMO.md](DEMO.md), [INVESTOR.md](INVESTOR.md) | Демо и питч |
| [ROADMAP_90_DAYS.md](ROADMAP_90_DAYS.md) | Фазы 1–4 |
| [TROUBLES.md](TROUBLES.md) | Аудит, gate, OPEN backlog |
| [CHANGELOG.md](CHANGELOG.md) | История релизов |
| [website/BRAND.md](website/BRAND.md) | Positioning, tone, CTAs |

## Health (как проверить, что работает)

```bash
# Docker (рекомендуется)
cp .env.example .env
docker compose up -d --build
curl -s http://localhost:8020/api/health

# Gate (из TROUBLES re-audit)
uv build
bash scripts/check-secrets.sh
pytest tests/test_code_tools.py tests/test_file_tools.py \
       tests/test_security_improvements.py tests/test_async_utils.py \
       tests/test_db_manager.py tests/test_production_hardening.py \
       tests/test_all.py::test_memory_manager -q

# Smoke UI
# http://localhost:8020/ — agent preview widget
# http://localhost:8020/login — admin + AGENT_PASSWORD
# POST /api/demo/public/agent-preview — live LLM (или mock без ключа)
```

Ожидаемо: health 200, pytest gate green, лендинг открывается на **8020**, import `web.server` без ошибок.
