# My Agent — Current State

## Session Date
2026-05-25

## UI/UX Polish (v3.2) ✅ COMPLETE

### Definition of Done

| Item | Status |
|------|--------|
| React SPA RU i18n (`src/i18n/ru.ts`) | ✅ |
| Shared UI primitives (Modal, Toast, PageHeader) | ✅ |
| Agents / Knowledge / MCP migrated to React | ✅ |
| Chat 2.1 (markdown, tools, feedback) | ✅ |
| Onboarding → `/app/onboarding` redirect | ✅ |
| Legacy routes 301 → `/app/*` | ✅ |
| Settings tabs (integrations / models / workspace) | ✅ |
| PWA manifest + service worker | ✅ |
| Playwright smoke tests (3 passed) | ✅ |
| UX events `POST /api/usage/event` | ✅ |
| Design system doc `web/frontend/DESIGN.md` | ✅ |

### Delivered
- **Pages:** `AgentsPage`, `KnowledgePage`, `McpPage`; updated Dashboard, Chat, Marketplace, Settings, Onboarding
- **Nav:** 10 пунктов в AppShell (RU)
- **Mobile:** chat threads drawer, safe-area, 44px touch targets

## Investor Demo Polish (v3.1) ✅ COMPLETE

### Definition of Done

| Item | Status |
|------|--------|
| `tpl_competitor_intelligence` template (featured) | ✅ |
| `action.n8n_webhook` node handler | ✅ |
| `POST /api/demo/run` + mock fallback | ✅ |
| Demo artifacts (`data/demo/`) | ✅ |
| Dashboard "Try 90s demo" + DemoModal | ✅ |
| Marketplace featured section + badges | ✅ |
| Onboarding step 4 inline demo run | ✅ |
| n8n optional service (`--profile demo`) | ✅ |
| `DEMO.md` investor script | ✅ |
| Frontend build + workflow tests green | ✅ |

### Delivered
- **Demo router:** `web/demo_router.py` — install template, stream prerecorded logs, serve DOCX
- **Template:** 7-node DAG (webhook → 2× research → merge → analyst → docs → n8n)
- **UI:** hero block, pulsing running nodes, ExecutionTimeline durations
- **Infra:** n8n on port 5678 under docker profile `demo`

## Phase 3 — B2B Workspaces + Analytics (v3.0) ✅ DoD COMPLETE

### Definition of Done

| Item | Status |
|------|--------|
| Team create + invite + accept | ✅ |
| Workspace-scoped workflows/sessions (RBAC) | ✅ |
| Google Sign-in | ✅ |
| Analytics UI (7/30d from DB) | ✅ |
| Admin UI (users, members, health) | ✅ |
| React onboarding with team step | ✅ |
| Alembic `004_teams` | ✅ |
| Tests (teams, usage, google auth) | ✅ 47 passed |
| Docs + CI | ✅ |

### Delivered
- **Teams:** `teams`, `team_members`, `team_invites`, `usage_events` (migration `004_teams`)
- **Workspace scoping:** `workspace_id` on workflows; sessions `{workspace}::{user}::{id}`
- **Team API:** `web/teams_router.py` — CRUD, invites, `active_team` cookie
- **RBAC:** owner / admin / member — `core/teams/permissions.py`
- **Google Sign-in:** `web/auth_router.py` (отдельно от integration OAuth)
- **Usage ledger:** `core/usage/tracker.py` — chat stream + workflow runs
- **Frontend:** Analytics, Admin, Onboarding, TeamSwitcher

### Phase 1 + Phase 2 (prior)
- Workflow engine, React SPA, 50 templates, chat sessions, email triggers, security hardening

### Out of scope (post-v3.1)
- Stripe billing, OIDC/SAML, Grafana sidecar, team-shared integration creds

## Test Commands
```bash
.venv/bin/python -m pytest tests/test_teams.py tests/test_usage.py tests/test_google_auth.py \
  tests/test_dod_closure.py tests/test_workflow_engine.py tests/test_marketplace.py -v
cd web/frontend && npm run build
docker compose --profile demo up -d --build   # http://127.0.0.1:8020
```

## Environment
- Web: `127.0.0.1:8020`
- n8n (demo): `127.0.0.1:5678`
- Python: 3.11+ | Node: 20+
- Redis: required in production (rate limits, sessions)
