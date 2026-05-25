# My Agent — Roadmap

## Phase 1: Foundation ✅ COMPLETE
**Theme:** Core architecture and basic functionality
**Deliverables:**
- Modular skill system with YAML frontmatter
- Tool registry with auto-registration
- Agent builder pattern
- CLI interface
- Basic memory (JSON-based)
- Web UI (FastAPI + vanilla HTML/JS)
- 3 initial agents (researcher, developer, marketer)

## Phase 2: Production Hardening ✅ COMPLETE
**Theme:** Fix 5 critical production issues
**Deliverables:**
- Async concurrency fix (`asyncio.to_thread()`)
- SQLite persistence with WAL + FTS5
- Retry logic with `jittered_backoff()`
- Safety guardrails (iteration budget, loop detection)
- Centralized logging with `RedactingFormatter`
- 27 tests passing (100% pass rate)

## Phase 3: Universal Assistant ✅ COMPLETE
**Theme:** One chat to rule them all
**Deliverables:**
- Universal agent with all 11 skills
- Auto-skill-selection based on user request
- Simplified chat UI (no agent selector)
- Welcome screen with example prompts

## Phase 4: Advanced Features (Current)
**Theme:** Streaming, auth, and scale
**Deliverables:**
- [ ] True streaming chat (token-by-token SSE)
- [ ] User authentication system (basic login)
- [ ] API rate limiting (slowapi)
- [ ] Redis caching for skill schemas
- [ ] Docker multi-stage build
- [ ] WebSocket support alternative to SSE

## Phase 5: Ecosystem (Future)
**Theme:** Third-party integrations and marketplace
**Deliverables:**
- [ ] Vector DB integration (ChromaDB) for RAG
- [ ] MCP (Model Context Protocol) server support
- [ ] Plugin marketplace / discovery
- [ ] Mobile-responsive UI
- [ ] OAuth (GitHub, Google login)

## Phase 6: Enterprise (Future)
**Theme:** Multi-tenant and team features
**Deliverables:**
- [ ] Multi-user sessions with isolation
- [ ] Team workspaces
- [ ] Usage analytics dashboard
- [ ] Admin panel
- [ ] SSO integration

## Milestone Tracking

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| v0.1 Foundation | 2026-05-15 | ✅ Complete |
| v0.5 Production | 2026-05-21 | ✅ Complete |
| v1.0 Universal | 2026-05-21 | ✅ Complete |
| v1.1 Streaming + Auth | 2026-05-28 | 🔄 In Planning |
| v1.2 Scale + Cache | 2026-06-04 | 📋 Planned |
| v2.0 Ecosystem | 2026-06-18 | 📋 Planned |

## Decision Log

1. **FastAPI over Flask/Django** — Better async support, automatic OpenAPI docs
2. **Vanilla HTML/JS over React** — Simpler deployment, no build step
3. **SQLite over PostgreSQL** — Zero-config, WAL mode handles concurrency
4. **LiteLLM over direct SDKs** — Unified interface for multiple providers
5. **ThreadPoolExecutor over asyncio** — Tool execution is CPU-bound
