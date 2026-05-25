# Handoff Instructions — My Agent

> **Date:** 2026-05-25
> **Session:** Full CLI TUI implementation + Retry optimization + Audit
> **Model:** kimi-k2.6 (opencode-go)
> **Total changes this session:** 12 new files, 8 modified files, 18 new tests

---

## Quick Start (New Device)

### 1. Clone / Copy Project
```bash
# If using git
git clone <repo-url>
cd my-agent

# If copying files — ensure you copy ALL files including:
# - config/
# - data/ (optional, contains session history)
# - .env (contains API keys!)
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
# Or:
pip install -e ".[dev]"
```

### 3. Configure API Keys
```bash
# Create .env file
cp .env.example .env
# Edit .env and add your keys:
# NEUROAPI_API_KEY=sk-...
# OPENROUTER_API_KEY=sk-or-...
# TAVILY_API_KEY=tvly-...
```

### 4. Run Tests
```bash
python agent.py test
# Should show: 429 passed, 1 skipped
```

### 5. Start Chat
```bash
python agent.py chat          # Default (fast model)
python agent.py chat --model smart
```

---

## What Was Done This Session

### New Files Created
| File | Purpose | Size |
|------|---------|------|
| `cli/tui.py` | Rich TUI engine | ~800 LOC |
| `tests/test_cli_tui.py` | TUI tests | ~200 LOC |
| `setup.bat` | Windows setup wizard | ~120 LOC |
| `agent.bat` | Windows launcher | ~20 LOC |
| `run.bat` | Alt Windows launcher | ~15 LOC |
| `WINDOWS_LAUNCH.md` | Windows docs | ~100 LOC |
| `AUDIT_2026.md` | Full audit report | ~600 LOC |
| `.env` | API keys configuration | ~8 lines |

### Modified Files
| File | What Changed |
|------|-------------|
| `agent.py` | `cmd_chat()` now uses Rich TUI, added `--session` arg, default command opens TUI |
| `core/config.py` | `load_agent_config()` with default path, added JSON support |
| `core/state_db.py` | Schema v2 with `language`, `cost_usd`, `tokens`, `compression_count` |
| `core/llm_gateway.py` | Fast overload fallback (skip retries), removed 30s cooldown |
| `core/runtime.py` | XML tool call fallback parser for non-structured responses |
| `config/agent.json` | `max_retries: 2`, `retry_base_delay: 1.5s` |
| `agent.py` (profiles) | Updated retry settings for all model profiles |

### Key Decisions Made
1. **Rich TUI over prompt_toolkit** — Rich is lighter, no PTY complexity, works on Windows
2. **UTF-8 via `sys.stdin.buffer`** — Fixes Windows CP1251 encoding issues
3. **Fast fallback on overload** — NeuroAPI often overloaded, don't waste 35s retrying
4. **Session IDs with millisecond precision** — `time.time() * 1000` prevents collision
5. **`.env` auto-loading** — `python-dotenv` at top of `agent.py` and `cli/tui.py`

---

## Architecture Overview (Current State)

```
my-agent/
├── agent.py              # CLI entry (argparse → TUI/chat/serve/test)
├── cli/tui.py            # Rich TUI (new!)
├── core/                 # 35 modules
│   ├── llm_gateway.py    # Async LLM with retry + fallback
│   ├── runtime.py        # Agent loop + parallel tool execution
│   ├── state_db.py       # SQLite WAL + FTS5 (schema v2)
│   ├── memory_manager.py # Dual SQLite/PostgreSQL
│   └── ...
├── skills/               # 30 skills (browser, vision, voice_io, web3, video, etc.)
├── web/                  # FastAPI + 10 HTML pages
│   ├── server.py         # Main API
│   ├── mcp_server.py     # MCP JSON-RPC 2.0
│   └── a2a_server.py     # Agent-to-Agent protocol
├── tests/                # 35 test files, 461 tests
└── agents/registry.json  # 10 agent profiles
```

---

## Next Steps / TODO

### Priority 1 (Critical for competitiveness)
- [ ] **VS Code Extension** — #1 request from audit, compete with Cursor
- [ ] **PWA / Service Worker** — Mobile support, offline capability
- [ ] **Windows UTF-8 permanently fixed** — Currently using workaround

### Priority 2 (High value)
- [ ] **React or HTMX frontend** — Replace vanilla JS web UI
- [ ] **Vector DB production** — ChromaDB for RAG (currently test-only)
- [ ] **Code indexing** — tree-sitter for semantic code search
- [ ] **Playwright E2E tests** — For web UI automation testing

### Priority 3 (Nice to have)
- [ ] **Desktop app (Tauri)** — 2MB Rust wrapper around web UI
- [ ] **Telegram/Discord bot** — Messaging skills already exist
- [ ] **MCP Hub marketplace** — Registry of MCP servers
- [ ] **SaaS hosting** — Multi-tenant PostgreSQL
- [ ] **Auto-tuning** — ML-based skill selection

---

## Testing Commands

```bash
# Fast tests (excludes slow/docker/postgres/e2e)
python agent.py test

# Full test suite
python -m pytest tests/ -v

# Specific modules
python -m pytest tests/test_cli_tui.py -v
python -m pytest tests/test_async.py -v
python -m pytest tests/test_production_hardening.py -v
```

---

## Known Issues / Gotchas

1. **Windows encoding** — If you see `UnicodeEncodeError`, ensure:
   - `chcp 65001` in .bat files
   - `PYTHONIOENCODING=utf-8` env var
   - `sys.stdout.reconfigure(encoding='utf-8')` in Python

2. **API key loading** — Must have `.env` file with `NEUROAPI_API_KEY` and `OPENROUTER_API_KEY`

3. **NeuroAPI overload** — Common between 03:00-06:00 MSK, fallback to OpenRouter works

4. **Skills not found warnings** — `voice_io`, `video_processing`, `web3` show warnings but don't break execution

5. **Docker not available on Windows** — Code execution falls back to subprocess (for now)

---

## API Keys Status (Working)

| Provider | Model | Latency | Status |
|----------|-------|---------|--------|
| NeuroAPI | gpt-5.4-nano | ~1.7s | ⚠️ Often overloaded |
| OpenRouter | owl-alpha | ~2.5s | ✅ Reliable |
| OpenRouter | claude-sonnet-4 | ~8s | ✅ Smart but slow |
| Tavily | Search | ~0.96s | ✅ Fast |

---

## Files to Preserve When Moving

**Must copy:**
- All `.py` files
- `config/` (agent configs)
- `agents/registry.json`
- `requirements.txt` / `pyproject.toml`
- `.env` (API keys!)
- `cli/` (new TUI)
- `tests/`

**Optional (can regenerate):**
- `data/` (session history, logs)
- `__pycache__/` (Python cache)
- `.pytest_cache/`

**Do NOT commit:**
- `.env` (contains secrets)
- `.agent_secret`
- `data/` (user data)

---

## Contact / Context

- **Full context:** Read `CONTEXT.md` first when resuming
- **Audit report:** See `AUDIT_2026.md` for competitive analysis
- **Windows guide:** See `WINDOWS_LAUNCH.md`
- **Architecture:** See `ARCHITECTURE.md`
- **Deployment:** See `DEPLOYMENT.md`

---

**Ready to continue!** Start with:
```bash
python agent.py chat
```

Or run setup wizard:
```bash
setup.bat  # Windows
```
