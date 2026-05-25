# Changelog — My Agent

## 3.3.1 — 2026-05-26 (CEO audits — sales readiness + product depth)

### Sales & onboarding (CEO audit B0–B4)
- Self-serve signup on `/login` → `/app/onboarding` (password 12+ chars)
- Template demo-run: `POST /api/workflow-templates/{id}/demo-run` + Marketplace button
- Plan tiers: `core/billing/plans.py`, quota check on run (429), Billing tab in Settings
- API Keys UI in Settings (list/create/delete via `/api/keys`)
- Workspace isolation: access checks on runs + `tests/test_workspace_isolation.py`
- Audit docs refreshed: `AUDIT_REPORT.md`, `AUDIT_2026.md`, `AUDIT_PRODUCT_2026.md`

### Builder & UX
- Condition branch modal + edge config side panel (removed `window.prompt`)
- Stub triggers hidden from palette (`trigger.email`, `trigger.new_lead`)
- Showcase graceful error state (no raw stack in subtitle)
- Lazy-loaded `WorkflowBuilder` + `MarketplacePage` (main bundle ~1.05 MB)

### Backend & infra
- Async workflow runs by default (`start_background()`); sync via `{"wait": true}`
- n8n provider in `integrations_registry.py`
- Schedule pause/resume API + WorkflowList UI (next/last run)
- `enable_memory` toggle on `agent.skill` node
- Agent healthcheck in docker-compose; `--profile monitoring` (Prometheus + Grafana)

### Deploy
- VDS: `vds-push` → `/opt/projects/my-agent`; prod runs bare uvicorn on `:8020` (see `SERVER.md`)

---

## 3.3.0 — 2026-05-26 (Architectural fix, iterations 1–2)

### Backend
- Kimi Code API as primary LLM (`core/kimi_provider.py`, `resolve_agent_model_config`)
- Docker entrypoint auto-seeds templates + generates demo DOCX on startup
- Workflow executor: failed actions no longer report run as `success`
- `agent.skill` node respects `"skill"` config key (singular)
- `action.webhook` supports GET; `action.n8n_webhook` added to NodeType enum
- Ghost tools removed from universal agent registry; SKILL.md for web3/voice_io/video_processing
- Seed upsert for draft templates; `tpl_lead_qualify` uses `trigger.webhook`
- Draft templates excluded from marketplace popular sort

### Frontend (RU)
- WorkflowBuilder full i18n (~40 keys)
- Marketplace admin Publish modal RU
- Dashboard integrations stat uses `configured`
- PublicTemplate install: toast on error, login redirect only on 401
- Onboarding friendly fallback when template install returns 404
- Removed orphan `AgentBuilderPage.tsx`

### Demo / ops
- 3 demo presets (competitor, beauty, lead) + sample JSON/DOCX artifacts
- A2A queue in Redis; WebSocket JWT auth
- Tests: `test_kimi_provider.py`, marketplace suite (25 passed in container)

---

## 3.2.0 — 2026-05-26 (UI/UX polish)

- React SPA on `/app/*` with RU i18n and PWA
- Demo-MVP showcase at `/showcase`
- Onboarding wizard, Dashboard hero, marketplace browse

---

## 3.1.0 and earlier

See git history and `SESSION_HISTORY.md`.
