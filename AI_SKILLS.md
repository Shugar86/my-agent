# AI Skills Used in Development

> Skills loaded from OpenCode system during My Agent development
> Date: 2026-05-21

---

## Overview

This project was built using multiple specialized AI skills from the OpenCode ecosystem. These skills provided domain-specific knowledge, patterns, and best practices that guided the architecture and implementation.

---

## Primary Skills Used

### 1. API Design (`api-design`)
**Usage:** REST API endpoints for FastAPI backend
**Applied:**
- Endpoint naming conventions
- Status code usage
- JSON request/response formats
- Error handling patterns

**Files affected:**
- `web/server.py` — All API endpoints
- `web/static/*.html` — Frontend API calls

---

### 2. Backend Patterns (`backend-patterns`)
**Usage:** Server-side architecture for Node.js/Express (adapted to Python)
**Applied:**
- Middleware patterns
- Error handling middleware
- Request validation
- Service layer abstraction

**Files affected:**
- `web/server.py` — Global exception handlers
- `core/orchestrator.py` — Service orchestration

---

### 3. Coding Standards (`coding-standards`)
**Usage:** Cross-project coding conventions
**Applied:**
- Naming conventions (snake_case for Python)
- Readability guidelines
- Immutability patterns
- Code quality review criteria

**Files affected:**
- All `.py` files in `core/`, `tools/`, `skills/`
- Builder pattern implementation

---

### 4. Frontend Design (`frontend-design`)
**Usage:** Web UI creation with high design quality
**Applied:**
- Dark theme design system
- CSS architecture
- Responsive layouts
- Component styling

**Files affected:**
- `web/static/index.html` — Dashboard
- `web/static/chat.html` — Chat interface
- `web/static/agents.html` — Agent management
- `web/static/settings.html` — Settings

**Design Decisions:**
- GitHub-inspired dark theme (#0d1117 background)
- Sidebar navigation pattern
- Card-based layouts
- Green (#238636) for primary actions
- Blue (#58a6ff) for accents

---

### 5. Next Best Practices (`next-best-practices`)
**Usage:** Next.js conventions (adapted to FastAPI + vanilla JS)
**Applied:**
- File structure conventions
- API route patterns
- Static file serving
- Error boundaries concept

**Files affected:**
- `web/server.py` — Route structure
- `web/static/` — Frontend organization

---

### 6. Tailwind CSS Patterns (`tailwind-css-patterns`)
**Usage:** Utility-first CSS patterns
**Applied:**
- Flexbox layouts
- Grid systems
- Spacing utilities
- Typography scale
- Color palettes

**Files affected:**
- All HTML files in `web/static/`
- Inline CSS using utility-like patterns

---

### 7. Vercel React Best Practices (`vercel-react-best-practices`)
**Usage:** React performance optimization (adapted to vanilla JS)
**Applied:**
- Component composition patterns
- State management concepts
- Event handling
- DOM manipulation efficiency

**Files affected:**
- `web/static/chat.html` — Message rendering
- `web/static/agents.html` — CRUD operations

---

### 8. Vercel Composition Patterns (`vercel-composition-patterns`)
**Usage:** React component composition (adapted to vanilla JS)
**Applied:**
- Modular component structure
- Props vs state concepts
- Render patterns

**Files affected:**
- `web/static/index.html` — Dashboard widgets
- `web/static/chat.html` — Chat components

---

### 9. Docker & Deployment (implied from general knowledge)
**Usage:** Containerization
**Applied:**
- Dockerfile best practices
- Multi-stage builds
- docker-compose orchestration
- Volume mounts

**Files affected:**
- `Dockerfile`
- `docker-compose.yml`
- `DEPLOYMENT.md`

---

## Secondary Skills Referenced

### 10. Graphify (`graphify`)
**Usage:** Codebase knowledge graph generation
**Applied:**
- Project structure analysis
- Community detection
- Architecture visualization
- Relationship mapping

**Files created:**
- `graphify-out/graph.html`
- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

**Key findings:**
- 277 nodes, 357 edges, 33 communities
- AgentBuilder is central architectural hub

---

### 11. Deep Research (from `deep_research` skill)
**Usage:** Research methodology
**Applied:**
- Multi-query approach
- Source synthesis
- Structured output format

**Files affected:**
- `skills/deep_research/SKILL.md`
- `tasks/deep-research.yaml`

---

## Skills NOT Used (but available)

The following skills were available but not directly utilized in this project:

### Frontend-Specific (not applicable)
- `android-clean-architecture` — Android/Kotlin only
- `compose-multiplatform-patterns` — Jetpack Compose
- `dart-flutter-patterns` — Flutter only
- `frontend-patterns` — General frontend (overlap with specific ones used)
- `frontend-slides` — Could have been used for slides skill
- `next-cache-components` — Next.js specific
- `next-upgrade` — Next.js migration
- `vercel-composition-patterns` — Already covered
- `vercel-react-best-practices` — Already covered

### Backend-Specific (different stack)
- `nodejs-backend-patterns` — Node.js stack
- `nestjs-patterns` — NestJS framework
- `nodejs-best-practices` — Node.js general
- `django-patterns` — Django framework
- `django-tdd` — Django testing
- `django-verification` — Django deployment
- `laravel-patterns` — PHP Laravel
- `laravel-tdd` — Laravel testing
- `laravel-verification` — Laravel deployment
- `springboot-patterns` — Java Spring Boot
- `springboot-tdd` — Spring Boot testing
- `springboot-verification` — Spring Boot deployment
- `java-coding-standards` — Java specific
- `kotlin-patterns` — Kotlin
- `kotlin-coroutines-flows` — Kotlin coroutines
- `kotlin-exposed-patterns` — Kotlin Exposed ORM
- `kotlin-ktor-patterns` — Ktor framework
- `kotlin-testing` — Kotlin testing
- `golang-patterns` — Go language
- `golang-testing` — Go testing
- `rust-patterns` — Rust
- `rust-testing` — Rust testing
- `perl-patterns` — Perl
- `perl-testing` — Perl testing
- `cpp-coding-standards` — C++
- `cpp-testing` — C++ testing
- `csharp-testing` — C# testing
- `dotnet-patterns` — .NET

### Database-Specific
- `prisma-cli` — Prisma ORM
- `prisma-client-api` — Prisma client
- `prisma-database-setup` — Prisma setup
- `prisma-postgres` — Prisma PostgreSQL

### Testing (pytest used instead)
- `python-testing` — Python testing patterns
- `tdd-workflow` — TDD methodology
- `e2e-testing` — Playwright E2E

### DevOps & CI/CD (not implemented)
- `verification-loop` — Session verification
- `strategic-compact` — Context compaction
- `plankton-code-quality` — Code quality enforcement

### AI/ML (not applicable)
- `ai-regression-testing` — AI testing
- `eval-harness` — Evaluation framework

### Other
- `accessibility` — WCAG compliance
- `seo` — Search optimization
- `code-tour` — CodeTour generation
- `hookify-rules` — Hook rules
- `agent-sort` — Agent sorting
- `configure-ecc` — ECC configuration
- `continuous-learning` — Learning system
- `council` — Decision council
- `customize-opencode` — OpenCode config
- `mcp-server-patterns` — MCP server

---

## Skill Effectiveness Rating

| Skill | Usage Frequency | Impact |
|-------|----------------|--------|
| `frontend-design` | High | Critical — UI quality |
| `coding-standards` | High | High — Code quality |
| `backend-patterns` | Medium | High — Architecture |
| `api-design` | Medium | Medium — API structure |
| `tailwind-css-patterns` | Medium | Medium — Styling |
| `next-best-practices` | Low | Low — File organization |
| `vercel-react-best-practices` | Low | Low — Performance concepts |
| `vercel-composition-patterns` | Low | Low — Component ideas |
| `graphify` | One-time | High — Architecture insight |
| `deep_research` | Referenced | Medium — Skill implementation |

---

## Skill Gaps Identified

During development, the following capabilities would have been helpful:

1. **Python Testing (`python-testing`)** — Could have improved test coverage
2. **TDD Workflow (`tdd-workflow`)** — Would have guided test-driven development
3. **Docker Best Practices** — Could have optimized Dockerfile
4. **FastAPI Patterns** — Specific skill for FastAPI architecture
5. **Async Programming** — For fixing blocking I/O issues
6. **Redis Patterns** — For memory management improvement

---

## How to Load Skills

For future development, skills can be loaded via:

```bash
# In OpenCode session
/load-skill <skill-name>

# Available skills:
/load-skill frontend-design
/load-skill coding-standards
/load-skill backend-patterns
/load-skill api-design
/load-skill python-testing
/load-skill tdd-workflow
```

Or check `available_skills` list in system prompt for current session.

---

## Notes for Continuation

When continuing development on another device:
1. Load `frontend-design` for UI work
2. Load `coding-standards` for code quality
3. Load `backend-patterns` for server architecture
4. Load `api-design` for new endpoints
5. Load `python-testing` for test writing
6. Load `tdd-workflow` for feature development

---

End of AI Skills Documentation
