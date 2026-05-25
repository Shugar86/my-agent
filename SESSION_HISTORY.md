# Session History — My Agent

---

## 2026-05-26 — Architectural fix (iterations 1–2)

> **Focus:** Close demo/marketplace gaps + engine correctness + RU UX polish  
> **Result:** v3.3.0 — Kimi live, honest workflow runs, RU builder, 52 templates seeded

### Iteration 1
- Kimi Code API integration (`api.kimi.com/coding/v1`, model `kimi-for-coding`)
- Entrypoint auto-seed + DOCX generation on container start
- Demo router: 3 presets; onboarding template IDs fixed
- A2A → Redis, WS JWT auth, Dashboard stats, showcase from API
- Marketplace install counts from DB; agents dedup; `/builder` → `/agents`

### Iteration 2
- P0: ghost tools removed; SKILL.md for web3/voice_io/video_processing
- P0: executor fail on action `{success:false}`; agent.skill `"skill"` key; webhook GET
- P0: draft tags on 3 misleading templates; n8n enum; lead qualify → webhook
- P1: WorkflowBuilder + Publish RU; integrations stat; PublicTemplate errors
- P1: EN string cleanup; onboarding 404 fallback; AgentBuilderPage removed

**Verify:** `docker compose up -d --build agent` → pytest 25 passed

Full changelog: **[CHANGELOG.md](./CHANGELOG.md)**

---

## 2026-05-25 — CLI TUI + Audit

> **Model:** kimi-k2.6 (opencode-go)
> **Start:** ~03:00 MSK
> **End:** ~04:00 MSK
> **Duration:** ~1 hour

---

## Task Log

### 1. Fix PPTX Export Bug
- **User:** "создай презентацию в pptx а то получается с пустыми слайдами"
- **Problem:** `_add_content_slide` in `skills/slides/skill.py` was only extracting first 500 chars from HTML
- **Fix:** Modified `_add_content_slide` to use explicit `title`/`content` keys, fallback HTML parsing, increased limit to 1000 chars
- **Result:** PPTX now correctly populated with tables, lists, columns
- **File:** `skills/slides/skill.py`

### 2. Create Standalone PPTX Script
- **User:** Asked for better PPTX creation
- **Action:** Created `scripts/create_presentation_fix.py` with full python-pptx implementation
- **Features:** 8 slides, tables, 3-column layouts, star-rating matrix, colored backgrounds
- **Result:** 41 KB PPTX with all content

### 3. CLI Chat Enhancement
- **User:** "давай как то улучшим взаимодействие человека с агентом в режиме cli"
- **Research:** Analyzed OpenCode (SolidJS TUI) and Hermes Agent (prompt_toolkit)
- **Decision:** Use Rich library for TUI
- **Created:** `cli/tui.py` (~800 LOC)
  - Welcome screen with ASCII art
  - Markdown + syntax highlighting rendering
  - Thinking spinner
  - Status bar (model, latency, messages)
  - 12 slash commands
  - Session persistence via StateDB
  - FTS5 search
  - Session forking
  - Model/agent switching on-the-fly
- **Tests:** `tests/test_cli_tui.py` (18 tests, all passing)

### 4. Fix CLI Input Encoding (Windows CP1251)
- **Problem:** `UnicodeEncodeError` when typing Russian text
- **Fix:** Use `sys.stdin.buffer.readline().decode('utf-8')` instead of `input()`
- **Result:** Russian text now works correctly

### 5. Optimize Retry Logic
- **Problem:** NeuroAPI overload caused 72-second waits before fallback
- **Fix:** 
  - Fast fallback on overload (skip retries)
  - Reduced `max_retries: 2` (was 3)
  - Reduced `retry_base_delay: 1.5s` (was 5s)
- **Result:** Fallback in 3-5s instead of 72s

### 6. Fix API Key Loading in CLI
- **Problem:** `.env` not loaded when running `agent.py chat`
- **Fix:** Added `python-dotenv` load at top of `agent.py` and `cli/tui.py`
- **Created:** `.env` file with working keys

### 7. Create Windows Launchers
- **Created:**
  - `agent.bat` — Double-click launcher
  - `run.bat` — Alternative launcher
  - `setup.bat` — Setup wizard with menu
  - `WINDOWS_LAUNCH.md` — Documentation

### 8. Audit 2026
- **User:** "сделай аудит проекта"
- **Action:** Full competitive audit
- **Created:** `AUDIT_2026.md`
- **Results:**
  - 27,179 LOC, 588 files
  - 30 skills, 10 agents, 461 tests
  - Competitiveness: 7.8/10
  - Leader in MCP/A2A: 9.7/10
  - Top-3 CLI agents: 8.6/10

### 9. Save History for Handoff
- **User:** "сохрани историю чата и документацию проекта"
- **Action:**
  - Updated `CONTEXT.md` with Phase 12 and 13
  - Created `HANDOFF.md` with setup instructions, architecture, TODO
  - Created this `SESSION_HISTORY.md`

---

## File Changes Summary

### New Files (8)
1. `cli/tui.py` — Rich TUI engine
2. `tests/test_cli_tui.py` — TUI tests
3. `setup.bat` — Windows setup wizard
4. `agent.bat` — Windows launcher
5. `run.bat` — Alt Windows launcher
6. `WINDOWS_LAUNCH.md` — Windows docs
7. `AUDIT_2026.md` — Audit report
8. `.env` — API keys

### Modified Files (7)
1. `agent.py` — Uses TUI, `--session` arg
2. `core/config.py` — `load_agent_config()`
3. `core/state_db.py` — Schema v2
4. `core/llm_gateway.py` — Fast fallback
5. `core/runtime.py` — XML tool parser
6. `skills/slides/skill.py` — Content slide fix
7. `config/agent.json` — Retry settings

### Tests
- **Before:** 411 tests
- **After:** 461 tests (429 passed fast subset)
- **New:** 18 CLI TUI tests

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| Rich over prompt_toolkit | Lighter, no PTY complexity, works on Windows |
| Fast overload fallback | NeuroAPI often overloaded, 35s retry wasted |
| Millisecond session IDs | Prevents collision in tests |
| `.env` auto-load | Users forget to load env vars |
| UTF-8 via stdin.buffer | Windows CP1251 breaks Russian input |
| Vanilla JS web UI | Simple but enough; React migration planned |

---

## Next Session Recommendations

**If starting fresh on new device:**
1. Read `HANDOFF.md`
2. Read `CONTEXT.md`
3. Run `python agent.py test`
4. Run `python agent.py chat`

**Top priority tasks:**
1. VS Code Extension (biggest competitive gap)
2. PWA / Service Worker
3. Windows UTF-8 permanent fix
4. React/HTMX frontend migration

---

## Resources Created This Session

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Full project history (updated) |
| `HANDOFF.md` | New device setup guide |
| `AUDIT_2026.md` | Competitive analysis |
| `WINDOWS_LAUNCH.md` | Windows-specific docs |
| `SESSION_HISTORY.md` | This file |

---

**Session complete. Project ready for handoff.**
