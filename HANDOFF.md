# Handoff Instructions — My Agent

> **Date:** 2026-05-27  
> **Version:** 3.5.0  
> **Docs index:** [docs/README.md](./docs/README.md)

---

## Quick Start

```bash
cd my-agent
cp .env.example .env
# Set KIMI_API_KEY=sk-kimi-... (primary LLM)

docker compose up -d --build
# Wait ~30s — entrypoint seeds templates + demo DOCX automatically

open http://127.0.0.1:8020/app   # login: admin / admin or self-serve register
```

For local production-like stack, set in `.env`:

```
ENV=production
DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
REDIS_URL=redis://127.0.0.1:6380/0
```

Run tests:

```bash
docker compose exec -T agent python -m pytest tests/test_production_v34.py tests/test_workflow_engine.py tests/test_workspace_isolation.py -q
```

---

## Current Product State (what to show)

| Surface | Status |
|---------|--------|
| `/login` | Register (12+ char password) → `/app/onboarding` |
| `/app/workflows` | List + schedule (next/last run, pause/resume) |
| `/app/workflows/:id` | Builder RU; branch modal; `enable_memory` on agent nodes |
| `/app/marketplace` | Browse + demo-run on templates |
| `/app/settings` | Integrations, API keys, billing plan |
| Workflow runs | Durable Redis queue; async by default |
| Prod health | `/api/health` → `"redis": true` when configured |

---

## Key Files (3.4.0)

| Area | Files |
|------|-------|
| Run queue | `core/workflow/run_queue.py`, `core/redis_client.py` |
| Prod DB | `core/db_manager.py` (fail-fast PG in production) |
| systemd | `deploy/my-agent.service` |
| Backup | `deploy/scripts/backup-db.sh` |
| Migration | `scripts/migrate_sqlite_to_postgres.py` |
| Monitoring | `deploy/monitoring/` (Grafana dashboard, Prometheus alerts) |
| Audits | `AUDIT_PRODUCTION_2026.md`, `AUDIT_PRODUCT_2026.md`, `SERVER.md` |

---

## Environment

| Variable | Required | Notes |
|----------|----------|-------|
| `ENV` | Prod | `production` enables PG + Redis requirements |
| `DATABASE_URL` | Prod | PostgreSQL only when `ENV=production` |
| `REDIS_URL` | Prod | Required for queue, rate limits, JWT revoke |
| `KIMI_API_KEY` | Demo/prod | Kimi Code API |

See `.env.example` for full list.

---

## Deploy (VDS)

**Stack:** systemd → uvicorn `:8020` + Docker `db` + `redis` + optional `monitoring`.

```bash
# Local → GitHub
git push origin main

# Local → VDS code
vds-push

# On VDS (see SERVER.md)
systemctl restart my-agent
curl -s http://127.0.0.1:8020/api/health   # expect redis: true
```

Path on VDS: `/opt/projects/my-agent/`  
Full runbook: [SERVER.md](./SERVER.md), [AUDIT_PRODUCTION_2026.md](./AUDIT_PRODUCTION_2026.md)

---

## Known Gaps (next iteration)

- Stripe payment integration (plan limits exist; no checkout)
- Worker service split (scheduler still in API process)
- External uptime check (UptimeRobot)
- HubSpot / Airtable connectors — see AUDIT_PRODUCT_2026.md
- 3 templates still `draft`
