# My Agent — Requirements

## Functional Requirements

### Core Agent System
- [x] Agent profiles with roles, skills, tools, and sub-agents
- [x] Universal Assistant with auto-skill-selection
- [x] LLM Gateway with OpenRouter support (DeepSeek V4 Flash)
- [x] Fallback model configuration
- [x] Tool registry with self-registration
- [x] Skill loader with YAML frontmatter parsing
- [x] Event bus for cross-component communication
- [x] Plugin manager for extensibility
- [x] Context compressor for long conversations

### Web Interface
- [x] FastAPI backend with REST API
- [x] Dashboard (index.html)
- [x] Chat interface with SSE streaming
- [x] Agent CRUD management (agents.html)
- [x] Settings page (settings.html)
- [x] Dark theme UI

### Persistence
- [x] SQLite state database with WAL mode
- [x] Session management (create, resume, list, delete)
- [x] Message storage with full history
- [x] FTS5 full-text search across messages
- [x] Automatic context compression for long sessions

### Reliability
- [x] Retry logic with jittered exponential backoff
- [x] Error classification (429, 401, 500, timeout)
- [x] Graceful fallback to secondary model
- [x] Structured error responses (no raw exceptions to user)
- [x] Iteration budget (max 90 tool calls)
- [x] Loop detection (same tool+args >3 times)
- [x] Tool error sanitization (strip structural tokens, cap at 2000 chars)

### Observability
- [x] Centralized logging setup
- [x] Rotating log files (agent.log, errors.log, web.log)
- [x] Secret redaction in logs (API keys, bearer tokens)
- [x] Per-session context tags in log lines
- [x] Suppression of noisy third-party loggers

## Non-Functional Requirements

### Performance
- [x] Skill loader caching (5-minute TTL, avoids disk reads per request)
- [x] Async concurrency: `asyncio.to_thread()` for blocking operations
- [x] Parallel sub-agent execution via `asyncio.gather()` + semaphore
- [x] SQLite WAL mode for concurrent readers + single writer

### Security
- [x] API key redaction in logs
- [x] No hardcoded secrets (env vars + config file)
- [x] Safe file writes (atomic where possible)

### Scalability
- [ ] Rate limiting on web API endpoints (TODO v1.1)
- [ ] Redis caching layer (TODO v1.2)
- [ ] Docker multi-stage build optimization (TODO v1.1)

## Skills Inventory (11 Total)

1. **deep_research** — Multi-query research with academic sources
2. **research** — Web search and content extraction
3. **parsing** — Text/data parsing utilities
4. **template** — Template-based content generation
5. **code_analysis** — Static code analysis
6. **code_execution** — Safe code execution
7. **web_automation** — Browser automation
8. **api_integration** — REST API connectivity
9. **data_analyst** — Pandas/matplotlib data analysis
10. **slides** — HTML → PPTX presentation generation
11. **docs** — HTML → DOCX/PDF document generation

## Tools Inventory (14 Total)

- deep_search, scholar_search, web_search, web_scrape
- file_read, file_write
- execute_code
- api_get, api_post, api_delete
- data_analyze, create_chart
- create_slides, create_document

## Known Limitations

1. No streaming token output (SSE sends full response at once)
2. No user authentication system
3. No rate limiting on API endpoints
4. Single-server deployment only (no horizontal scaling)
5. Windows-specific path handling in some areas
