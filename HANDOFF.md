# Handoff Instructions — My Agent

> **Date:** 2026-05-26  
> **Version:** 3.3.0  
> **Last session:** Architectural fix iterations 1–2 (Kimi, honest engine, RU builder)

---

## Quick Start

```bash
cd my-agent
cp .env.example .env
# Set KIMI_API_KEY=sk-kimi-... (primary LLM)

docker compose up -d --build
# Wait ~30s — entrypoint seeds templates + demo DOCX automatically

open http://127.0.0.1:8020/app   # login: admin / admin
```

Optional manual seed:

```bash
docker compose exec agent python scripts/seed_workflow_templates.py
docker compose exec agent python scripts/generate_demo_artifact.py
```

Run tests:

```bash
docker compose exec -T agent python -m pytest tests/test_marketplace.py tests/test_kimi_provider.py -q
```

---

## Current Product State (what to show)

| Surface | Status |
|---------|--------|
| `/app/` Dashboard | 4 stat cards; integrations count from `configured` |
| `/app/chat` | Kimi universal agent, ~61 real tools (no ghost stubs) |
| `/app/workflows/:id` | Builder fully RU |
| `/app/marketplace` | Browse + admin Publish RU; draft templates hidden from popular |
| `/app/onboarding` | 4-step wizard + 90s demo; 404 template fallback |
| `/showcase` | Public Demo-MVP (7 verticals) |
| Workflow runs | **Failed** if action node returns `{success: false}` |

---

## Key Files Changed (3.3.0)

| Area | Files |
|------|-------|
| LLM | `core/kimi_provider.py`, `core/llm_gateway.py`, `core/config.py` |
| Engine | `core/workflow/executor.py`, `nodes/agent.py`, `nodes/action.py`, `models.py` |
| Registry | `agents/registry.json` (ghost tools removed) |
| Skills | `skills/web3/SKILL.md`, `voice_io/SKILL.md`, `video_processing/SKILL.md` |
| Seed | `scripts/entrypoint.sh`, `scripts/seed_workflow_templates.py` |
| Frontend | `WorkflowBuilder.tsx`, `ru.ts`, `Dashboard.tsx`, `MarketplacePage.tsx` |
| Demo | `web/demo_router.py`, `data/demo/*.json`, `*.docx` |

---

## Environment

| Variable | Required | Notes |
|----------|----------|-------|
| `KIMI_API_KEY` | Yes (prod demo) | Kimi Code API; rotate if exposed |
| `OPENROUTER_API_KEY` | Fallback | Optional secondary LLM |
| `TAVILY_API_KEY` | Demo research | Mock works without |
| `TELEGRAM_BOT_TOKEN` | Workflows | Telegram actions fail honestly without it |

See `.env.example` for full list.

---

## Deploy (VDS)

```bash
# Local
git commit && vds-push

# Prod
vds-deploy my-agent
vds-logs my-agent
```

Path on VDS: `/opt/projects/my-agent/`  
Docs: [SERVER.md](./SERVER.md), [DEMO.md](./DEMO.md), [CHANGELOG.md](./CHANGELOG.md)

---

## Known Gaps (next iteration)

- Full E2E for all 52 templates requires integration credentials
- 3 templates still `draft` (gmail digest, notion sync, invoice followup)
- `window.prompt` for condition branch labels in builder (plan: modal)
