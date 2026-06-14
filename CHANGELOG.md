# Changelog — My Agent

## [Unreleased]

---

## 4.0.1 — 2026-06-14 (Documentation sync)

### Changed
- Документация синхронизирована с v4.0.0: ARCHITECTURE, PROJECT_GUIDE, DEPLOYMENT, SERVER, BRAND, docs/README.
- Удалены мёртвые ссылки на `AUDIT_*.md`, `HANDOFF.md`; добавлен `website/README-DEPRECATED.md`.
- `pyproject.toml` version → 4.0.0 (выровнен с README/CHANGELOG).
- Kimi-ссылки убраны из operational docs; primary LLM — OpenRouter.

---

## 4.0.0 — 2026-05-28 (Agent OS pivot + landing redesign)

### Product narrative
- **Pivot:** «Competitor Intelligence за 90 сек» → «AI-оператор для бизнеса за 2 минуты».
- **Landing redesign:** 6 секций вместо 9. Hero = AgentPreviewWidget (live LLM). Убраны Pricing, Problems, Proof strip. Добавлены showcase cards (3 live кейса с persona snippets).
- **Dashboard:** chat-first hero, primary CTA → `/app/chat`, stats скрыты при пустой БД.
- **DemoModal:** PlaygroundDemo → AgentPreviewWidget.
- **Onboarding step 1:** PlaygroundDemo → AgentPreviewWidget.

### New endpoints
- `POST /api/demo/public/agent-preview` — live LLM генерация AI-оператора из текстового описания задачи (deepseek-chat-v3-free via OpenRouter).
- `POST /api/demo/public/agent-chat` — follow-up chat с preview-агентом.
- Rate limit: 5 preview + 10 chat req/IP/hour (Redis middleware).
- Guard: 503 при отсутствии `OPENROUTER_API_KEY`; prompt injection protection; regex JSON extraction.

### Kimi cleanup
- Удалены `api_key` / `base_url` Kimi из всех 10 агентов в `registry.json`.
- Все агенты используют `model: "balanced"` → OpenRouter через `configurator.py`.
- Удалены Kimi-ссылки из i18n, AgentsPage, `.env.example`.

### Chat reliability (Phase 2)
- **SSE persistence:** `chat_stream` теперь сохраняет `full_response` через `session.add_assistant_message()` перед `persist_session()`.
- **Unified storage:** `sessions_router` читает messages из PG (MemoryManager) когда `DATABASE_URL` = PostgreSQL. Singleton `_get_pg_memory()`.
- **SSE error handling:** ChatPage обрабатывает `event.type === 'error'`.
- **Real mode:** `REAL_MODE_LLM_KEYS` расширен на `NEUROAPI_API_KEY`; Tavily больше не обязателен.

### Deploy fixes
- `.env.example`: `AGENT_PASSWORD=change-me-12ch` (>= 12 символов).
- `deploy/.env.example`: добавлены `AGENT_PASSWORD`, `TAVILY_API_KEY`.
- `REAL_MODE_SEARCH_KEYS` удалён (dead code).

### Docs
- README, DEMO.md, INVESTOR.md переписаны под новый narrative.
- Удалены orphan i18n ключи (problems, pricing, old stats).

---

## 3.5.3 — 2026-05-27 (TROUBLES remediation + re-audit)

### Security & build
- **pyproject.toml**: `[tool.setuptools.packages.find]` — `uv build` / `pip install -e .` работают.
- **JS execution**: `run_javascript()` через file mount в Docker (без shell injection).
- **file_tools**: sandbox `AGENT_WORKSPACE` + `validate_safe_path_or_error`.
- **CI**: `scripts/check-secrets.sh` + GitHub workflow `secrets-check.yml`.

### Runtime & production
- **user_manager**: SQLite через `asyncio.to_thread`; fail-closed admin при `ENV=production` без `AGENT_PASSWORD`.
- **feedback**: lazy `_get_db()` вместо import-time singleton.
- **web/server.py**: `_init_agent_runtime()` на startup; `CORS_ORIGINS`; `get_client_ip()` (X-Forwarded-For); Prometheus request metrics middleware.
- **memory_manager**: `replace_messages` / atomic compress — без дубликатов сообщений.
- **alembic/env.py**: миграции читают `DATABASE_URL`.
- **wizard**: отклонение пароля &lt; 12 символов.

### Fixes (medium backlog)
- MCP skill URI path traversal; demo_router CWD; MCP stdio lock; session_cache rate-limit key; agent_store KeyError guard; docker-compose без deprecated `version:`.

### Docs & tests
- Re-audit gate **60/60 PASS** — см. [TROUBLES.md](TROUBLES.md) § Re-audit post-remediation.
- `tests/conftest.py`, `tests/test_file_tools.py`.

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
