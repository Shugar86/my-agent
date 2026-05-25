# My Agent — развёртывание на VDS

> Сервер: `159.195.31.95` | Путь: `/opt/projects/my-agent/`  
> Статус: **v3.0 B2B Ready** (Phase 1–3 complete)

---

## Порты (этот сервер)

| Сервис | Host | Контейнер | Конфликты |
|--------|------|-----------|-----------|
| Web UI | `127.0.0.1:8020` | 8020 | ❌ 8000 занят magikbook-api |
| PostgreSQL | `127.0.0.1:5437` | 5432 | ❌ 5436 infodon, 5435 coffeeman |
| Redis | `127.0.0.1:6380` | 6379 | magikbook-redis без host-порта |

---

## Быстрый старт (Docker)

```bash
cd /opt/projects/my-agent

# 1. Конфиг
cp .env.example .env
# Заполнить: OPENROUTER_API_KEY, AGENT_SECRET_KEY, AGENT_PASSWORD
# Опционально: GOOGLE_AUTH_CLIENT_ID/SECRET для Sign-in with Google

# 2. Собрать frontend (если менялся web/frontend/)
cd web/frontend && npm install && npm run build && cd ../..

# 3. Seed workflow-шаблонов (первый раз)
python3 scripts/seed_workflow_templates.py

# 4. Запуск (миграции Alembic включая 004_teams — автоматически)
docker compose up -d --build

# 5. Проверка
curl -s http://127.0.0.1:8020/api/health | python3 -m json.tool
```

Логин: `admin` / `AGENT_PASSWORD` из `.env`, или **Sign in with Google** (если настроен OAuth).

---

## UI routes (Phase 3)

| URL | Назначение |
|-----|------------|
| `/login` | JWT login + Google |
| `/app` | Dashboard |
| `/app/workflows` | Workflow list + builder |
| `/app/marketplace` | Templates |
| `/app/analytics` | Usage dashboard |
| `/app/admin` | Team members + system health (owner/admin) |
| `/app/onboarding` | Team setup + integrations + first template |
| `/metrics` | Prometheus scrape |

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
cd web/frontend && npm run build
```

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

Документация: `ROADMAP_90_DAYS.md`, `SECURITY.md`, `.planning/STATE.md`, `ARCHITECTURE.md`.
