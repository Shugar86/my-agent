# Handoff Instructions — My Agent

> **Date:** 2026-05-26  
> **Version:** 3.3.1  
> **Last session:** CEO audits — sales readiness + product depth

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

Optional manual seed:

```bash
docker compose exec agent python scripts/seed_workflow_templates.py
docker compose exec agent python scripts/generate_demo_artifact.py
```

Run tests:

```bash
docker compose exec -T agent python -m pytest tests/test_marketplace.py tests/test_workflow_engine.py tests/test_workspace_isolation.py -q
```

---

## Current Product State (what to show)

| Surface | Status |
|---------|--------|
| `/login` | Register (12+ char password) → `/app/onboarding` |
| `/app/` Dashboard | 4 stat cards; integrations count from `configured` |
| `/app/chat` | Kimi universal agent, ~61 real tools |
| `/app/workflows` | List + schedule section (next/last run, pause/resume) |
| `/app/workflows/:id` | Builder RU; branch modal; edge config; `enable_memory` on agent nodes |
| `/app/marketplace` | Browse + demo-run button on templates |
| `/app/settings` | Integrations, API keys, billing plan, models |
| `/showcase` | Public Demo-MVP (7 verticals) |
| Workflow runs | Async by default; failed actions → failed run |

---

## Key Files (3.3.1)

| Area | Files |
|------|-------|
| Billing | `core/billing/plans.py`, `web/workflow_router.py` (quota) |
| Async runs | `core/workflow/executor.py` (`start_background`) |
| Schedule | `core/scheduler_manager.py`, `WorkflowList.tsx` |
| Builder UX | `WorkflowBuilder.tsx`, `types/workflow.ts` (`paletteHidden`) |
| Template demo | `core/workflow/template_demo.py`, `MarketplacePage.tsx` |
| Audits | `AUDIT_REPORT.md`, `AUDIT_2026.md`, `AUDIT_PRODUCT_2026.md` |
| Monitoring | `docker-compose.yml` (`--profile monitoring`) |

---

## Environment

| Variable | Required | Notes |
|----------|----------|-------|
| `KIMI_API_KEY` | Yes (prod demo) | Kimi Code API |
| `OPENROUTER_API_KEY` | Fallback | Optional secondary LLM |
| `TAVILY_API_KEY` | Demo research | Mock works without |
| `TELEGRAM_BOT_TOKEN` | Workflows | Telegram actions fail honestly without it |
| `DATABASE_URL` | Prod recommended | PostgreSQL in compose; SQLite fallback local |

See `.env.example` for full list.

---

## Deploy (VDS)

Prod runs **bare uvicorn** on `127.0.0.1:8020` (not root docker-compose service).

```bash
# Local
git commit && vds-push

# Sync work tree on VDS (if hook didn't update)
ssh vds-root 'cd /opt/projects/my-agent && git fetch /root/git/my-agent.git main && git reset --hard FETCH_HEAD'

# Restart
ssh vds-root 'cd /opt/projects/my-agent && pkill -f "uvicorn web.server:app --host 127.0.0.1 --port 8020"; sleep 2; nohup .venv/bin/python -m uvicorn web.server:app --host 127.0.0.1 --port 8020 >> /var/log/my-agent.log 2>&1 &'

curl -s http://127.0.0.1:8020/api/health
```

Path on VDS: `/opt/projects/my-agent/`  
Docs: [SERVER.md](./SERVER.md), [DEMO.md](./DEMO.md), [CHANGELOG.md](./CHANGELOG.md), [AUDIT_PRODUCT_2026.md](./AUDIT_PRODUCT_2026.md)

Optional monitoring:

```bash
cd /opt/projects/my-agent && docker compose --profile monitoring up -d prometheus grafana
```

---

## Known Gaps (next iteration)

- Stripe payment integration (plan limits exist; no checkout)
- HubSpot / Airtable / Linear connectors (roadmap in AUDIT_PRODUCT_2026)
- Full E2E for all 52 templates requires integration credentials
- 3 templates still `draft` (gmail digest, notion sync, invoice followup)
- VDS prod uses SQLite unless `DATABASE_URL` set — migrate to PostgreSQL
