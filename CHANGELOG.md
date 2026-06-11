# Changelog — My Agent

## 3.5.3 — 2026-06-11 (Documentation refresh)

- Синхронизированы версии и факты во всех основных документах (**3.5.2** product baseline).
- **OpenRouter** зафиксирован как primary LLM; Kimi — optional fallback.
- Обновлены счётчики: 10 агентов, 33 skills, 52+ marketplace templates, 21 node types.
- [docs/README.md](docs/README.md): таблица ключевых фактов, ссылка на `WINDOWS_LAUNCH.md`, пометка `graphify-out/` как не-документация.
- [SERVER.md](SERVER.md): актуальные UI routes (Settings tabs вместо `/app/agents`).
- [WINDOWS_LAUNCH.md](WINDOWS_LAUNCH.md): убраны персональные пути, добавлен Docker quick start.

---

## 3.5.2 — 2026-05-27 (Live chat + OpenRouter + Postgres stability)

### LLM & Demo
- Primary LLM switched from Kimi to **OpenRouter** (`openrouter/owl-alpha` + `balanced` profile in `agents/registry.json` and `config/agent.json`).
- Tavily is the default web search backend for live demo runs when `TAVILY_API_KEY` is present.
- `core/kimi_provider.py`: `resolve_kimi_base_url()` no longer leaks `KIMI_BASE_URL` for non-Kimi models (prevents OpenRouter key being sent to Kimi endpoint).

### Critical bugfix: Chat completely broken in Docker
- Root cause: In production (`DATABASE_URL` set), `MemoryManager` selected PostgreSQL backend, but `PGStateManager._pool` was never initialized (no call to `connect()` at startup) and the live DB had a legacy `sessions` schema (`agent_id` + `messages` blob) incompatible with the current `PGStateManager` expectations.
- Result: every `/api/chat` and orchestrator run blew up with `AttributeError: 'NoneType' object has no attribute 'acquire'` (or `UndefinedColumnError`).

### Fixes
- `core/pg_state.py`: Added `ensure_connected()` (lazy asyncpg pool initialization on first use) + `_migrate_from_legacy_if_needed()` that safely drops old tables and recreates the modern schema on first connection (chat history is ephemeral for the demo).
- All call sites updated to use `await memory.ensure_session()` / `await memory.persist_session()`.
- Minor runtime blockers resolved: `from ddgs import` → `from duckduckgo_search import`, f-string backslash syntax error in `skills/browser/skill.py`, `.dockerignore` now excludes `.env`.
- Verified end-to-end inside the real Docker stack: `POST /api/chat` returns real LLM answers via OpenRouter.

---

## 3.5.1 — 2026-05-27 (Documentation)

- Added [docs/README.md](docs/README.md) as documentation index
- Streamlined [README.md](README.md) — removed inline changelog blocks, fixed port **8020**
- Updated [PROJECT_GUIDE.md](PROJECT_GUIDE.md), [ARCHITECTURE.md](ARCHITECTURE.md), [DEPLOYMENT.md](DEPLOYMENT.md)
- Removed obsolete session/meta docs (`CONTEXT.md`, `SESSION_HISTORY.md`, `AI_SKILLS.md`, audit snapshots)

---

## 3.4.1 — 2026-05-26 (UX sprint — investor funnel)

### Frontend — status & demo UX
- `FeatureTag` component + `featureRegistry.ts` (Live / Beta / Preview / Coming soon)
- `PlaygroundDemo` + `DemoStepper` embedded in `/app/showcase` and onboarding step 1
- Marketplace template demo-run: ExecutionTimeline modal instead of raw JSON
- WorkflowBuilder: demo mode banner (`?demo=mock`), breadcrumbs
- `demoFallback.ts` for offline showcase data on Dashboard/Showcase

### Frontend — navigation IA
- AppShell: Main (Dashboard, Workflows, Marketplace, Chat) + Secondary (Analytics, Settings)
- Agents / Knowledge / MCP moved to Settings tabs (`?tab=agents|knowledge|mcp`)
- Redirects from legacy `/app/agents`, `/app/knowledge`, `/app/mcp`
- Sidebar tagline: «Autonomous Workflow OS»

### Public landing
- `#problems` section (3 pain cards)
- `#live-demo` iframe embed of `/demo`
- `#marketplace-preview` from `/api/public/templates?featured=true&limit=3`

### Polish
- Chat: loading skeleton, Beta badge, «Try 90s demo» in empty state
- Analytics: workflow names, empty CTA to `/demo`
- Settings billing: Stripe `coming-soon` badge
- E2E: landing sections, authenticated showcase playground, billing badge

---

## 3.4.0 — 2026-05-26 (CEO audit — Production readiness)

### Ops
- systemd unit: [deploy/my-agent.service](deploy/my-agent.service)
- PostgreSQL mandatory when `ENV=production` (fail-fast, no SQLite)
- Redis required in production startup; health `redis: true`
- Daily backup script + restore runbook in SERVER.md

### Execution
- Durable workflow run queue via Redis RPOPLPUSH ([core/workflow/run_queue.py](core/workflow/run_queue.py))
- Orphaned runs marked failed on restart; stale processing jobs recovered

### Observability
- Grafana dashboard + Prometheus alert rules (`--profile monitoring`)
- Structured workflow run logging (`run_id`, `workflow_id`)

### Migration
- [scripts/migrate_sqlite_to_postgres.py](scripts/migrate_sqlite_to_postgres.py) for one-time VDS migration
- [AUDIT_PRODUCTION_2026.md](AUDIT_PRODUCTION_2026.md)

---

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

See git history and [docs/README.md](docs/README.md).
