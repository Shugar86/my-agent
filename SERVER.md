# My Agent — развёртывание на VDS

> Сервер: `159.195.31.95` | Путь: `/opt/projects/my-agent/`  
> Статус: **v3.2 UI/UX Polish** (React SPA RU, PWA, legacy → `/app/*` redirects)

---

## Порты (этот сервер)

| Сервис | Host | Контейнер | Конфликты |
|--------|------|-----------|-----------|
| Web UI | `127.0.0.1:8020` | 8020 | ❌ 8000 занят magikbook-api |
| PostgreSQL | `127.0.0.1:5437` | 5432 | ❌ 5436 infodon, 5435 coffeeman |
| Redis | `127.0.0.1:6380` | 6379 | magikbook-redis без host-порта |
| n8n (demo) | `127.0.0.1:5678` | 5678 | только с `--profile demo` |

---

## Быстрый старт (Docker)

```bash
cd /opt/projects/my-agent

# 1. Конфиг
cp .env.example .env
# Заполнить: OPENROUTER_API_KEY, AGENT_SECRET_KEY, AGENT_PASSWORD
# Опционально: GOOGLE_AUTH_CLIENT_ID/SECRET, N8N_WEBHOOK_URL

# 2. Собрать frontend (если менялся web/frontend/)
cd web/frontend && npm install && npm run build && cd ../..

# 3. Seed workflow-шаблонов + demo-артефакт (первый раз)
python3 scripts/seed_workflow_templates.py
python3 scripts/generate_demo_artifact.py

# 4. Запуск (миграции Alembic — автоматически)
docker compose up -d --build

# 5. Проверка
curl -s http://127.0.0.1:8020/api/health | python3 -m json.tool
```

### Investor demo (с n8n)

```bash
docker compose --profile demo up -d --build
docker compose exec agent python scripts/seed_workflow_templates.py
docker compose exec agent python scripts/generate_demo_artifact.py
# http://127.0.0.1:8020/app → "Try 90s demo"
# n8n UI: http://127.0.0.1:5678 (admin / demo)
```

Сценарий для инвестора: **[DEMO.md](./DEMO.md)**.

Логин: `admin` / `AGENT_PASSWORD` из `.env`, или **Sign in with Google** (если настроен OAuth).

---

## UI routes

| URL | Назначение |
|-----|------------|
| `/login` | JWT login + Google |
| `/welcome` | Маркетинговый лендинг |
| `/app` | Панель (dashboard) |
| `/app/chat` | Чат (markdown, SSE, `/run workflow`) |
| `/app/workflows` | Workflow list + builder |
| `/app/marketplace` | Templates |
| `/app/agents` | Управление агентами |
| `/app/knowledge` | База знаний (RAG) |
| `/app/mcp` | MCP-серверы |
| `/app/analytics` | Usage dashboard |
| `/app/admin` | Team members + system health (owner/admin) |
| `/app/settings` | Интеграции, модели, профиль workspace |
| `/app/onboarding` | Team → integrations → template → 90s demo |
| `/app/builder` | Agent Builder wizard |
| `/metrics` | Prometheus scrape |

Legacy paths (`/chat`, `/agents`, `/knowledge`, `/mcp`, `/onboarding`, …) → **301** на `/app/*` для авторизованных пользователей. Новый пользователь без onboarding → `/app/onboarding`.

### Demo API

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/demo/run` | Запуск Competitor Intelligence (mock fallback без ключей) |
| GET | `/api/demo/artifact/{filename}` | Скачать DOCX-артефакт |
| GET | `/api/demo/sample` | Метрики demo run (ROI, tokens, duration) |

---

## Team API (Phase 3)

```bash
# Список команд (cookie access_token)
curl -s http://127.0.0.1:8020/api/teams -b cookies.txt

# Usage summary за 7 дней
curl -s "http://127.0.0.1:8020/api/usage/summary?period=7d" -b cookies.txt
```

Personal team создаётся автоматически при первом login. Active workspace — cookie `active_team`.

---

## Локальная разработка (без Docker)

```bash
cd /opt/projects/my-agent
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env

.venv/bin/python scripts/seed_workflow_templates.py
.venv/bin/uvicorn web.server:app --host 127.0.0.1 --port 8020 --reload
```

---

## Тесты

```bash
cd /opt/projects/my-agent
.venv/bin/python -m pytest \
  tests/test_teams.py tests/test_usage.py tests/test_google_auth.py \
  tests/test_dod_closure.py tests/test_workflow_engine.py tests/test_marketplace.py -v
cd web/frontend && npm run build && npm run test:e2e
```

Playwright smoke tests требуют запущенный сервер на `:8020`. Auth-тесты: `E2E_USER=admin E2E_PASS=... npm run test:e2e`.

---

## Структура по фазам

| Phase | Компонент | Путь |
|-------|-----------|------|
| 1 | Workflow Engine | `core/workflow/` |
| 1 | API routes | `web/workflow_router.py` |
| 2 | React SPA | `web/frontend/` → `web/static/app/` |
| 2 | 25 templates | `scripts/seed_workflow_templates.py` |
| 3 | Teams / RBAC | `core/teams/`, `web/teams_router.py` |
| 3 | Usage ledger | `core/usage/`, `web/usage_router.py` |
| 3 | Google auth | `web/auth_router.py` |
| 3 | Migration | `alembic/versions/004_teams.py` |
| Demo | Investor demo | `web/demo_router.py`, `DEMO.md`, `data/demo/` |
| Demo | n8n node | `action.n8n_webhook` in `core/workflow/nodes/action.py` |
| Demo | Featured template | `tpl_competitor_intelligence` in seed script |
| UI v3.2 | React SPA RU + PWA | `web/frontend/` → `web/static/app/` |
| UI v3.2 | i18n + shared UI | `web/frontend/src/i18n/`, `src/components/ui/` |
| UI v3.2 | UX events API | `POST /api/usage/event` in `web/usage_router.py` |
| UI v3.2 | Playwright E2E | `web/frontend/e2e/smoke.spec.ts` |

Дизайн-система: `web/frontend/DESIGN.md`. OpenCode reference: `DESIGN-opencode-reference.md`.
