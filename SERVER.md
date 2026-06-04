# My Agent — развёртывание на VDS

> Сервер: `159.195.31.95` | Путь: `/opt/projects/my-agent/`  
> Статус: **v3.5.2** (OpenRouter primary, systemd, PostgreSQL, Redis queue)

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

---

## Порты (этот сервер)

| Сервис | Host | Контейнер | Конфликты |
|--------|------|-----------|-----------|
| Web UI | `127.0.0.1:8020` | 8020 | ❌ 8000 занят magikbook-api |
| PostgreSQL | `127.0.0.1:5437` | 5432 | ❌ 5436 infodon, 5435 coffeeman |
| Redis | `127.0.0.1:6380` | 6379 | magikbook-redis без host-порта |
| n8n (demo) | `127.0.0.1:5678` | 5678 | только с `--profile demo` |

---

## Быстрый старт (Docker, dev/staging)

```bash
cd /opt/projects/my-agent

cp .env.example .env
# OPENROUTER_API_KEY, AGENT_SECRET_KEY, AGENT_PASSWORD

# Frontend (если менялся web/frontend/)
cd web/frontend && bun install && bun run build && cd ../..

docker compose up -d --build
# entrypoint автоматически seed шаблонов + demo DOCX

curl -s http://127.0.0.1:8020/api/health | python3 -m json.tool
```

### Investor demo (с n8n)

```bash
docker compose --profile demo up -d --build
# http://127.0.0.1:8020/showcase#playground  — канонический demo
# n8n UI: http://127.0.0.1:5678 (admin / demo)
```

Сценарий: **[DEMO.md](./DEMO.md)** · **[INVESTOR.md](./INVESTOR.md)**.

---

## UI routes

| URL | Назначение |
|-----|------------|
| `/showcase#playground` | **Канонический demo** — Competitor Intelligence 90s |
| `/showcase` | 7 vertical cases + playground |
| `/demo` | Shortcut на playground (вторичный) |
| `/login` | JWT login + Google |
| `/app` | Dashboard |
| `/app/chat` | Чат (markdown, SSE) |
| `/app/workflows` | Workflow list + builder |
| `/app/marketplace` | Templates |
| `/app/settings` | Integrations, API keys, billing, agents/knowledge/MCP (tabs) |
| `/app/onboarding` | 4-step wizard |
| `/metrics` | Prometheus scrape |

Редиректы: `/app/agents` → `settings?tab=agents`, `/welcome` → `/`.

---

## Demo API

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/demo/run` | Competitor Intelligence (auth, mock fallback) |
| POST | `/api/demo/public/run` | Public demo для `/showcase` и `/demo` |
| GET | `/api/demo/public/runs/{id}` | Polling статуса public demo run |
| GET | `/api/demo/artifact/{filename}` | Скачать DOCX-артефакт |
| POST | `/api/leads/showcase` | Lead form → `data/showcase_leads.jsonl` |

---

## Локальная разработка (без Docker)

```bash
cd /opt/projects/my-agent
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env

export DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
export REDIS_URL=redis://127.0.0.1:6380/0

.venv/bin/uvicorn web.server:app --host 127.0.0.1 --port 8020 --reload
```

---

## Тесты

```bash
.venv/bin/python -m pytest tests/test_demo_flow.py tests/test_marketplace.py -q

# E2E (сервер на :8020):
cd web/frontend && bun run test:e2e
```

---

## См. также

- [DEPLOYMENT.md](./DEPLOYMENT.md) — общий deploy guide
- [deploy/README.md](./deploy/README.md) — Render/Railway/Fly
- [SECURITY.md](./SECURITY.md) — production checklist
- [docs/README.md](./docs/README.md) — индекс документации
