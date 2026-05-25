# My Agent — Roadmap

## Phase 1: Foundation ✅ COMPLETE
**Theme:** Core architecture and basic functionality

## Phase 2: Production Hardening ✅ COMPLETE
**Theme:** Async, persistence, retry, guardrails, logging

## Phase 3: Universal Assistant ✅ COMPLETE
**Theme:** One chat, auto-skill-selection

## Phase 4: Advanced Features ✅ COMPLETE
**Theme:** Streaming, auth, and scale
**Deliverables:**
- [x] True streaming chat (SSE + WebSocket)
- [x] User authentication system (JWT + bcrypt)
- [x] API rate limiting (slowapi + Redis)
- [x] Redis caching
- [x] Docker multi-stage build
- [x] WebSocket support
- [x] MCP Server + Client
- [x] A2A Protocol
- [x] Rich CLI TUI

## Phase 5: Ecosystem ✅ MOSTLY COMPLETE
**Theme:** Integrations and marketplace
**Deliverables:**
- [x] Vector DB integration (ChromaDB) for RAG
- [x] MCP server support
- [x] Plugin marketplace (stub → workflow templates in Phase 7)
- [ ] Mobile-responsive UI / PWA
- [x] OAuth (Google — Phase 7)

## Phase 6: Enterprise (Future)
**Theme:** Multi-tenant and team features
- [ ] Team workspaces
- [ ] Usage analytics dashboard
- [ ] SSO integration

## Phase 7: Business Product (90-Day Plan) 🔄 IN PROGRESS
**Theme:** Workflow automation + marketplace MVP — compete with ASCN.ai
**See:** `ROADMAP_90_DAYS.md`

### Phase 7.1 (Days 1–30) — ✅ COMPLETE
- [x] Workflow Engine v1 (JSON DAG executor)
- [x] 5 integrations: Telegram, Gmail, Sheets, Slack, Notion
- [x] React Flow workflow builder
- [x] Dashboard 1-click templates
- [x] Onboarding wizard (3 steps)
- [x] Marketplace MVP (12 templates)
- [x] Alembic migrations for workflows
- [x] Schedule triggers + condition routing + validate API

### Phase 7.2 (Days 31–60) — ✅ COMPLETE
- [x] Full UI redesign (React SPA shell at `/app/*`)
- [x] Production workflow canvas (timeline, edge labels, validate, runs panel)
- [x] Agent Builder 2.0 (visual wizard)
- [x] Chat 2.0 (threads + streaming)
- [x] 25+ marketplace templates + ratings + publish API
- [x] Marketing landing integration
- [x] Docker frontend build

### Phase 7.3 (Days 61–90)
- [ ] Multi-user roles + team workspaces
- [ ] Observability dashboard
- [ ] Stripe / SaaS pricing

## Milestone Tracking

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| v0.1 Foundation | 2026-05-15 | ✅ Complete |
| v0.5 Production | 2026-05-21 | ✅ Complete |
| v1.0 Universal | 2026-05-21 | ✅ Complete |
| v1.5 MCP + TUI | 2026-05-25 | ✅ Complete |
| v2.0 Workflow MVP | 2026-06-25 | ✅ Complete |
| v2.5 Marketplace | 2026-07-25 | ✅ Complete |
| v3.0 SaaS Ready | 2026-08-25 | 📋 Planned |

## Decision Log

1. **FastAPI over Flask/Django** — Better async support
2. **Hybrid frontend** — React SPA at `/app/*` for all main screens; vanilla HTML for login/onboarding legacy
3. **SQLite + PostgreSQL dual mode** — Zero-config dev, prod scale
4. **LiteLLM** — Unified multi-provider LLM gateway
5. **JSON DAG over custom DSL** — Simpler Phase 1, visual editor maps 1:1
