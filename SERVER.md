# My Agent — развёртывание на VDS

> Сервер: `159.195.31.95` | Путь: `/opt/projects/my-agent/`  
> Статус: **v4.0.0** (Agent OS pivot, OpenRouter, agent preview)

---

## Prod runtime

**Stack:** `systemd` → bare uvicorn `:8020` + Docker `db` + `redis` + optional `monitoring` profile.

```bash
# Деплой кода
vds-push

ssh vds-root 'cd /opt/projects/my-agent && git fetch /root/git/my-agent.git main && git reset --hard FETCH_HEAD'

# .env (обязательно в prod)
# ENV=production
# OPENROUTER_API_KEY=sk-or-v1-...
# DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
# REDIS_URL=redis://127.0.0.1:6380/0
# AGENT_PASSWORD >= 12 символов

docker compose up -d db redis
# Не поднимайте контейнер `agent` на VDS — API работает через systemd (порт 8020).
docker compose --profile monitoring up -d
cp deploy/my-agent.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now my-agent

curl -s http://127.0.0.1:8020/api/health | python3 -m json.tool
# Ожидаем: "redis": true
```

Frontend собирается локально и коммитится в `web/static/app/` (на VDS нет bun).

### Backup PostgreSQL

```bash
# Ручной бэкап
bash deploy/scripts/backup-db.sh

# Cron (ежедневно 03:00)
echo '0 3 * * * root /opt/projects/my-agent/deploy/scripts/backup-db.sh >> /var/log/my-agent-backup.log 2>&1' \
  > /etc/cron.d/my-agent-backup
```

**Restore (≈15 мин):**

```bash
gunzip -c /opt/backups/my-agent/agent_db_YYYYMMDD_HHMMSS.sql.gz | psql "$DATABASE_URL"
systemctl restart my-agent
```

### Миграция SQLite → PostgreSQL (один раз)

```bash
cd /opt/projects/my-agent
export DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
.venv/bin/python scripts/migrate_sqlite_to_postgres.py --dry-run
.venv/bin/python scripts/migrate_sqlite_to_postgres.py
```

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
# Заполнить: OPENROUTER_API_KEY, AGENT_SECRET_KEY, AGENT_PASSWORD (>= 12)
# Опционально: GOOGLE_AUTH_CLIENT_ID/SECRET, N8N_WEBHOOK_URL, TAVILY_API_KEY

# 2. Собрать frontend (если менялся web/frontend/)
cd web/frontend && bun install && bun run build && cd ../..

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
# http://127.0.0.1:8020/ — live agent preview на лендинге
# n8n UI: http://127.0.0.1:5678 (admin / demo)
```

Сценарий для инвестора: **[DEMO.md](./DEMO.md)**.

Логин: `admin` / `AGENT_PASSWORD` из `.env`, или **Sign in with Google** (если настроен OAuth).

---

## UI routes

| URL | Назначение |
|-----|------------|
| `/` | Лендинг: hero + live agent preview |
| `/demo` | Agent preview (shortcut) |
| `/showcase` | 7 vertical cases + agent preview widget |
| `/login` | JWT login + Google |
| `/app` | Dashboard (chat-first hero) |
| `/app/chat` | Multi-thread SSE chat |
| `/app/workflows` | Workflow list + builder |
| `/app/marketplace` | Templates |
| `/app/settings` | API keys, agents, knowledge, MCP, billing |
| `/app/onboarding` | 4-step wizard |
| `/app/analytics` | Usage dashboard |
| `/app/admin` | Team members + system health (owner/admin) |
| `/metrics` | Prometheus scrape |

Legacy paths (`/app/agents`, `/app/knowledge`, `/app/mcp`, `/app/builder`) → redirect на `/app/settings?tab=...`.

### Demo API

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/demo/public/agent-preview` | Live LLM agent preview (public) |
| POST | `/api/demo/public/agent-chat` | Follow-up chat с preview-агентом |
| POST | `/api/demo/public/run` | Workflow demo для showcase |
| GET | `/api/demo/public/runs/{id}` | Polling статуса public demo run |
| POST | `/api/demo/run` | Workflow demo (auth) |
| GET | `/api/demo/artifact/{filename}` | Скачать DOCX-артефакт |
| POST | `/api/leads/showcase` | Lead form → `data/showcase_leads.jsonl` |

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
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
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
cd web/frontend && bun run build && bun run test:e2e
```

Playwright smoke tests требуют запущенный сервер на `:8020`. Auth-тесты: `E2E_USER=admin E2E_PASS=... bun run test:e2e`.

---

## Структура по фазам

| Phase | Компонент | Путь |
|-------|-----------|------|
| 1 | Workflow Engine | `core/workflow/` |
| 1 | API routes | `web/workflow_router.py` |
| 2 | React SPA | `web/frontend/` → `web/static/app/` |
| 2 | 25+ templates | `scripts/seed_workflow_templates.py` |
| 3 | Teams / RBAC | `core/teams/`, `web/teams_router.py` |
| 3 | Usage ledger | `core/usage/`, `web/usage_router.py` |
| 3 | Google auth | `web/auth_router.py` |
| 4 | Agent preview | `web/demo_router.py` — public LLM endpoints |
| Demo | n8n node | `action.n8n_webhook` in `core/workflow/nodes/action.py` |
| UI | Playwright E2E | `web/frontend/e2e/` |

Дизайн-система: `web/frontend/DESIGN.md`.
