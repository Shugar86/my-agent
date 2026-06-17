# Deployment Guide

> My Agent — Production Deployment  
> Version: **4.0.0**

**VDS:** см. [SERVER.md](./SERVER.md) — порт **8020**.  
**Investor demo:** [DEMO.md](./DEMO.md).

---

## Quick Start (Docker)

```bash
cp .env.example .env
# OPENROUTER_API_KEY=sk-or-v1-...  (live agent preview; без ключа — mock fallback)
# AGENT_PASSWORD >= 12 символов

docker compose up -d --build
curl -s http://127.0.0.1:8020/api/health
```

Открыть: http://localhost:8020/

С n8n для демо: `docker compose --profile demo up -d --build`

---

## Prerequisites

- Docker + Docker Compose
- 2 GB RAM minimum
- `OPENROUTER_API_KEY` (demo работает без ключей — mock fallback)

Production additionally:

- PostgreSQL 16
- Redis 7
- TLS termination (nginx/Caddy) — см. `deploy/Caddyfile.prod`

---

## Environment

```bash
cp .env.example .env
```

| Variable | Production |
|----------|------------|
| `ENV` | `production` |
| `DATABASE_URL` | PostgreSQL (required) |
| `REDIS_URL` | Redis (required) |
| `OPENROUTER_API_KEY` | Primary LLM |
| `AGENT_SECRET_KEY` | Random 32+ chars |
| `AGENT_PASSWORD` | ≥ 12 chars |

`docker-compose.yml` выставляет `ENV=production` и подключает db/redis автоматически.

---

## Local development (without full compose)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

export DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
export REDIS_URL=redis://127.0.0.1:6380/0

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

Frontend rebuild after UI changes:

```bash
cd web/frontend && bun install && bun run build
```

---

## Tests before deploy

```bash
python -m pytest tests/ -q

# Smoke (in container):
docker compose exec -T agent python -m pytest \
  tests/test_production_v34.py tests/test_marketplace.py -q

bash scripts/check-secrets.sh
```

---

## Production stack

| Component | Path |
|-----------|------|
| Docker prod | `deploy/docker-compose.prod.yml` |
| systemd | `deploy/my-agent.service` |
| Monitoring | `docker compose --profile monitoring up -d` |
| Backup | `deploy/scripts/backup-db.sh` |

Подробный runbook: [deploy/README.md](./deploy/README.md).

---

## Checklist

- [ ] `.env` с уникальными `AGENT_PASSWORD`, `AGENT_SECRET_KEY`
- [ ] `DATABASE_URL` + `REDIS_URL` заданы
- [ ] `curl http://127.0.0.1:8020/api/health` → `redis: true`
- [ ] TLS перед публичным доступом
- [ ] `cd web/frontend && bun run build` после изменений UI
- [ ] Не коммитить `.env`, `logs/`, runtime `data/`

---

## Troubleshooting deploy

| Issue | Fix |
|-------|-----|
| Health `redis: false` | Start redis service, check `REDIS_URL` |
| PG connection refused | `docker compose up db -d`, port 5437 on host |
| 502 behind nginx | Agent listens on **8020**, not 8000 |
| Templates empty | `docker compose exec agent python scripts/seed_workflow_templates.py` |
| Agent preview mock only | Set `OPENROUTER_API_KEY` in `.env`, restart |

См. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).
