# My Agent — Technical Documentation

> Last updated: 2026-05-26
> Version: 3.4.0 (CEO audit — production readiness)
> Author: AI Assistant

---

## Investor Demo (90 seconds)

**Killer use-case:** Competitor Intelligence — webhook → 2 parallel research agents →
SWOT analysis → DOCX report → n8n hook. Replaces ~4 hours of analyst work.

```bash
docker compose up -d --build
# Entrypoint auto-runs seed + DOCX generation on first start
# Open http://localhost:8020/app → "Try 90s demo"
```

Manual re-seed (optional):

```bash
docker compose exec agent python scripts/seed_workflow_templates.py
docker compose exec agent python scripts/generate_demo_artifact.py
```

Full script, talking points, and troubleshooting: **[DEMO.md](./DEMO.md)**.

**Demo-MVP showcase (recommended):** `http://localhost:8020/showcase` — 7 vertical
production cases, live playground, lead CTA. Quick ref: **[INVESTOR.md](./INVESTOR.md)**.

Mock fallback works without API keys — safe for live investor presentations.

### Web UI (v3.2)

Единый React SPA на `/app/*` (интерфейс на русском). Legacy static (`/agents`, `/chat`, …) редиректит в SPA.

| URL | Назначение |
|-----|------------|
| `/login` | JWT + Google OAuth |
| `/app/` | Панель (dashboard, demo hero) |
| `/app/chat` | Чат (markdown, tool bubbles, feedback) |
| `/app/workflows` | Список workflows + builder (`/app/workflows/:id`) — **RU UI** |
| `/app/marketplace` | Маркетплейс шаблонов |
| `/app/agents` | CRUD агентов |
| `/app/knowledge` | База знаний (RAG) |
| `/app/mcp` | MCP-серверы |
| `/app/settings` | Интеграции, модели, API keys, billing, профиль workspace |
| `/app/onboarding` | 4-step wizard + 90s demo |
| `/app/showcase` | Demo-MVP vertical cases (auth) |
| `/showcase` | Demo-MVP showcase (public, no auth) |
| `/demo` | Public Competitor Intelligence demo |
| `/welcome` | Маркетинговый лендинг |

Дизайн-система: [`web/frontend/DESIGN.md`](web/frontend/DESIGN.md). Сборка: `cd web/frontend && bun run build`.

### Changelog 3.4.0 (2026-05-26) — Production readiness

**Ops:** systemd on VDS, PostgreSQL + Redis required in prod, daily `pg_dump` backup, Grafana/Prometheus alerts.

**Execution:** durable workflow run queue (Redis RPOPLPUSH); orphaned runs marked failed on restart.

Docs: [AUDIT_PRODUCTION_2026.md](./AUDIT_PRODUCTION_2026.md), [SERVER.md](./SERVER.md).

### Changelog 3.3.1 (2026-05-26) — CEO audits

**Sales readiness:** signup → onboarding, plan limits, template demo-run, API keys + billing UI, workspace isolation tests.

**Product depth:** async workflow runs, schedule pause/resume UI, builder branch modal + edge panel, `enable_memory` on agent nodes, lazy bundle split, n8n registry, monitoring profile.

Roadmap: [AUDIT_PRODUCT_2026.md](./AUDIT_PRODUCT_2026.md).

### Changelog 3.3.0 (2026-05-26) — Architectural fix

**Iteration 1 — gap closure**
- Kimi Code API (`KIMI_API_KEY`, `core/kimi_provider.py`) as primary LLM for all agents
- Docker entrypoint: auto-seed 52 templates + 3 demo DOCX on startup
- Demo presets: competitor / beauty / lead; onboarding template mapping fixed
- A2A queue → Redis; WebSocket JWT auth; Dashboard 4 stat cards
- Marketplace: real install counts; showcase featured from API

**Iteration 2 — correctness + RU polish**
- Removed ghost tools from `universal` registry (voice_io/video/web3 stubs not in tool list)
- Added `SKILL.md` for `web3`, `voice_io`, `video_processing` (skills load when enabled)
- Executor: `action.*` with `{success: false}` → run status **failed** (no soft-success)
- `agent.skill` respects config field `"skill"` (singular)
- `action.webhook` supports `method=GET`; `action.n8n_webhook` in NodeType enum
- 3 misleading templates tagged `draft`; `tpl_lead_qualify` → `trigger.webhook`
- WorkflowBuilder + Marketplace Publish modal fully RU; Dashboard integrations stat fix
- PublicTemplate: toast on install error (401 only → login); orphan `AgentBuilderPage` removed

**Verify after deploy**
```bash
docker compose up -d --build agent
docker compose exec -T agent python -m pytest tests/test_production_v34.py tests/test_marketplace.py -q
curl -s http://127.0.0.1:8020/api/health
# Production: ENV=production requires DATABASE_URL + REDIS_URL
```

---

## 1. Project Overview

My Agent is a modular AI agent system with a visual workflow builder, marketplace,
multi-agent orchestration, and deep research capabilities.

### Key Features
- **Universal Assistant** — one chat for everything, Kimi K2.6, ~61 real tools (no phantom stubs)
- **7 Specialized Agents** — researcher, developer, marketer, data_analyst, slides, docs, universal
- **30+ Skills** — deep_research, research, parsing, RAG, browser, web3, voice_io, …
- **Workflow Engine** — visual DAG builder (React Flow), 21+ node types, **async runs**, honest status
- **Marketplace** — 52 templates, demo-run preview, featured section
- **Investor Demo** — `POST /api/demo/run` with 3 presets + prerecorded fallback + DOCX
- **n8n Integration** — `action.n8n_webhook` node (optional `--profile demo` stack)
- **Auto-Agent Factory** — LLM analyzes tasks and spawns sub-agents dynamically
- **Graphify Integration** — codebase knowledge graph with community detection

### Tech Stack
| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI Gateway | Kimi Code API (primary) + LiteLLM/OpenRouter fallback |
| Frontend | React 18 + TypeScript + Vite + React Flow (`/app/*`), RU i18n, PWA |
| Data | PostgreSQL / SQLite, Redis |
| Container | Docker + Docker Compose (+ optional n8n profile) |
| Testing | pytest + Playwright E2E (`web/frontend/e2e/`) |

---

## 2. Architecture

```
my-agent/
├── agent.py              # CLI entry point
├── web/
│   ├── server.py         # FastAPI backend
│   ├── frontend/         # React SPA source (Vite)
│   │   ├── src/          # Pages, components, i18n (RU)
│   │   ├── e2e/          # Playwright smoke tests
│   │   └── DESIGN.md     # Product design system
│   ├── static/
│   │   ├── app/          # Built SPA (npm run build)
│   │   └── login.html    # Auth page (legacy static)
│   └── Dockerfile
├── core/                 # Core framework modules
│   ├── builder.py        # AgentBuilder (fluent pattern)
│   ├── runtime.py        # AgentRuntime (execution loop)
│   ├── orchestrator.py   # Task routing & delegation
│   ├── sub_agents.py     # Parallel agent execution
│   ├── auto_agent_factory.py  # Dynamic agent spawning
│   ├── agent_store.py    # Agent profile CRUD
│   ├── llm_gateway.py    # LLM abstraction (litellm)
│   ├── skill_loader.py   # Skill discovery & loading
│   ├── tool_registry.py  # Tool registration
│   ├── memory_manager.py # Session memory (JSON)
│   ├── event_bus.py      # Event system
│   ├── plugin_manager.py # Plugin discovery
│   ├── context_compressor.py  # Context compression
│   ├── config.py         # Configuration management
│   └── logger.py         # Logging utilities
├── skills/               # Skill modules
│   ├── research/         # Web research skill
│   ├── deep_research/    # Multi-query deep research
│   ├── parsing/          # Content parsing
│   ├── template/         # Template engine
│   ├── code_analysis/    # Code review & analysis
│   ├── code_execution/   # Code execution sandbox
│   ├── web_automation/   # Web scraping
│   ├── api_integration/  # API connector skill
│   ├── data_analyst/     # Data analysis (pandas/matplotlib)
│   ├── slides/           # Presentation generation
│   └── docs/             # Document generation (DOCX/PDF)
├── tools/                # Tool implementations
│   ├── web_tools.py      # Web search/scrape
│   ├── file_tools.py     # File I/O
│   ├── code_tools.py     # Code execution
│   ├── api_connector.py  # HTTP API tools
│   ├── deep_search_tools.py  # Academic search
│   ├── mcp_client.py     # MCP protocol client
│   ├── data_tools.py     # Data analysis tools
│   ├── slides_tools.py   # Presentation tools
│   ├── docs_tools.py     # Document tools
│   └── auto_agents_tools.py  # Auto-agent tools
├── agents/               # Agent registry
│   └── registry.json     # 7 agent profiles
├── config/               # Configuration
│   ├── agent.json        # Main config (API keys, model)
│   └── models.yaml       # Model presets
├── tasks/                # Predefined task templates
│   ├── research-course.yaml
│   ├── code-review.yaml
│   ├── api-test.yaml
│   └── deep-research.yaml
├── tests/                # Test suite
│   ├── test_all.py       # Core module tests (12 tests)
│   └── test_skills_builder.py  # Builder tests (6 tests)
├── graphify-out/         # Knowledge graph outputs
│   ├── graph.html        # Interactive visualization
│   ├── GRAPH_REPORT.md   # Graph analysis report
│   └── graph.json        # Raw graph data
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker orchestration
├── Dockerfile            # Container definition
└── plans/                # Architecture plans
    └── my-agent-web-ui.md
```

---

## 3. Core Concepts

### 3.1 Agent
An agent is a configured LLM instance with:
- **Role** (system prompt)
- **Model** (primary + fallback)
- **Skills** (capabilities)
- **Tools** (functions)
- **Memory** (session persistence)

### 3.2 Skill
A skill is a module providing domain-specific capabilities:
- `SKILL.md` — documentation and usage
- `skill.py` — implementation
- Registers tools via `register_tools()`

### 3.3 Tool
A tool is a Python function callable by the LLM:
- Registered in `tool_registry.py`
- Schema auto-generated from docstrings
- Can return text, files, or structured data

### 3.4 Builder Pattern
```python
from core.builder import AgentBuilder

agent = (AgentBuilder()
    .set_model({"primary": "openrouter/...", "api_key": "..."})
    .set_role("You are a helpful assistant")
    .set_skills(["research", "parsing"])
    .set_tools(["web_search", "file_write"])
    .set_memory({"enabled": True, "scope": "agent"})
    .enable_events(True)
    .enable_compression(True)
    .build())
```

### 3.5 Orchestrator
Routes user requests:
1. **Handoff** — single agent execution
2. **Parallel Delegate** — multiple sub-agents + result synthesis

### 3.6 Auto-Agent Factory
```python
from core.auto_agent_factory import AutoAgentFactory

factory = AutoAgentFactory(store, llm_config)
result = factory.spawn_for_task("Research AI trends and write summary")
```
Process:
1. LLM analyzes task → identifies sub-tasks
2. Creates temporary agent configs
3. Runs agents in parallel (ThreadPoolExecutor)
4. Synthesizes results
5. Cleans up temp agents

---

## 4. API Reference

### 4.1 REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard HTML |
| GET | `/chat` | Chat interface HTML |
| GET | `/agents` | Agent management HTML |
| GET | `/settings` | Settings HTML |
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/{id}` | Get agent by ID |
| POST | `/api/agents` | Create agent |
| PUT | `/api/agents/{id}` | Update agent |
| DELETE | `/api/agents/{id}` | Delete agent |
| POST | `/api/agents/{id}/duplicate` | Duplicate agent |
| POST | `/api/chat` | Send message (JSON response) |
| POST | `/api/chat/stream` | Send message (SSE streaming) |
| GET | `/api/config` | Get system config |
| POST | `/api/config` | Update config |

### 4.2 Chat Request Format
```json
{
  "message": "Hello!",
  "agent_id": "universal",
  "auto_agents": false
}
```

### 4.3 Chat Response Format
```json
{
  "response": "Agent's response text"
}
```

### 4.4 Error Response
```json
{
  "error": "Error description",
  "detail": "Additional details"
}
```

---

## 5. Agent Registry

All agents defined in `agents/registry.json`:

| ID | Name | Icon | Skills | Purpose |
|----|------|------|--------|---------|
| **universal** | Universal Assistant | 🤖 | 11 skills | Auto-selects tools for any task |
| researcher | Researcher | 🔍 | deep_research, research, parsing | Deep research & analysis |
| developer | Developer | 💻 | code_analysis, code_execution | Code review & dev |
| marketer | Marketer | 📢 | research, template, web_automation | Marketing & content |
| data_analyst | Data Analyst | 📊 | data_analyst, code_execution | Data analysis & charts |
| slides | Slides Agent | 🎨 | slides, template | Presentations (HTML→PPTX) |
| docs | Docs Agent | 📄 | docs, template | Documents (HTML→DOCX/PDF) |

---

## 6. Skills Reference

| Skill | File | Tools | Capabilities |
|-------|------|-------|--------------|
| **deep_research** | `skills/deep_research/skill.py` | deep_search, scholar_search, web_scrape | Multi-query academic research |
| **research** | `skills/research/skill.py` | web_search, web_scrape | General web research |
| **parsing** | `skills/parsing/skill.py` | web_scrape, file_read | Content extraction |
| **template** | `skills/template/skill.py` | file_write | Template engine |
| **code_analysis** | `skills/code_analysis/skill.py` | file_read, file_write | Code review, bug finding |
| **code_execution** | `skills/code_execution/skill.py` | execute_code | Python/bash/JS execution |
| **web_automation** | `skills/web_automation/skill.py` | web_search, web_scrape | Web scraping |
| **api_integration** | `skills/api_integration/skill.py` | api_get, api_post, api_delete | HTTP API calls |
| **data_analyst** | `skills/data_analyst/skill.py` | file_read, file_write, execute_code | Pandas, matplotlib, statistics |
| **slides** | `skills/slides/skill.py` | file_read, file_write, web_search | HTML slides → PPTX |
| **docs** | `skills/docs/skill.py` | file_read, file_write, web_search | HTML → DOCX/PDF |

---

## 7. Configuration

### 7.1 Main Config (`config/agent.json`)
```json
{
  "model": {
    "primary": "openrouter/deepseek/deepseek-v4-flash:free",
    "api_key": "sk-or-v1-...",
    "fallback": "openrouter/deepseek/deepseek-chat",
    "params": {
      "temperature": 0.5,
      "max_tokens": 4096
    }
  }
}
```

### 7.2 Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Fallback | OpenRouter API key (optional if Kimi set) |
| `KIMI_API_KEY` | Primary | Kimi Code API key (`sk-kimi-...`) |
| `KIMI_BASE_URL` | No | Override base URL (default: `https://api.kimi.com/coding/v1`) |
| `PYTHONIOENCODING` | No | Set to `utf-8` for Windows |

### 7.3 Agent Config Fields
```json
{
  "id": "unique-id",
  "name": "Display Name",
  "icon": "🤖",
  "description": "What this agent does",
  "role": "System prompt / instructions",
  "model": {
    "primary": "model-id",
    "api_key": "${ENV_VAR}",
    "fallback": "fallback-model",
    "params": {"temperature": 0.5}
  },
  "skills": ["skill1", "skill2"],
  "tools": ["tool1", "tool2"],
  "sub_agents": ["agent-id-1"],
  "memory": {"enabled": true, "scope": "agent"},
  "output": {"format": "markdown", "path": "output/file.md"}
}
```

---

## 8. Development Guide

### 8.1 Project Setup

```bash
# Clone project
cd my-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Verify setup
python -m pytest tests/ -v
```

### 8.2 Running the Server

```bash
# Set API key
export OPENROUTER_API_KEY="sk-or-v1-..."

# Run server
python -m uvicorn web.server:app --host 0.0.0.0 --port 8000

# Open browser
# http://localhost:8000
```

### 8.3 Docker Deployment

```bash
# Build and run
docker-compose up --build

# Or manual
docker build -t my-agent .
docker run -p 8000:8000 -e OPENROUTER_API_KEY=... my-agent
```

### 8.4 Adding a New Skill

1. Create directory: `skills/my_skill/`
2. Add `SKILL.md` — documentation
3. Add `skill.py` — implementation with `register_tools()` function
4. Register in `agents/registry.json` under agent's `skills` list

Example `skill.py`:
```python
def my_tool(param: str) -> str:
    """Tool description for LLM"""
    return f"Result: {param}"

def register_tools(registry):
    registry.register("my_tool", my_tool)
```

### 8.5 Adding a New Agent

1. Add entry to `agents/registry.json`
2. Or use API: `POST /api/agents`

---

## 9. Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_all.py -v

# Run with coverage
pytest tests/ --cov=core --cov-report=html
```

Current test coverage: **20 tests** passing
- `test_all.py` — 12 tests (core modules)
- `test_skills_builder.py` — 6 tests (builder pattern)

---

## 10. Known Issues & Limitations

### Resolved in 3.3.0
- Ghost tools in chat (speak_text, web3, video_*) — removed from universal tool list
- Workflow runs marked success when Telegram/Slack failed — executor now fails honestly
- WorkflowBuilder / Publish modal EN strings — RU i18n complete
- Dashboard integrations stat always 0 — fixed (`configured` field)

### Remaining
1. **Blocking I/O in async endpoints** — some sync paths in orchestrator
2. **E2E templates** — most templates need integration credentials for full delivery
3. **Draft templates** — 3 templates tagged `draft` until gmail/notion nodes added
4. Windows encoding issues with emojis in CLI

---

## 11. File Map

| File | Purpose | Lines |
|------|---------|-------|
| `agent.py` | CLI entry | ~100 |
| `web/server.py` | FastAPI backend | ~150 |
| `core/builder.py` | Agent builder | ~100 |
| `core/runtime.py` | Execution loop | ~115 |
| `core/orchestrator.py` | Task router | ~55 |
| `core/llm_gateway.py` | LLM abstraction | ~40 |
| `core/skill_loader.py` | Skill discovery | ~80 |
| `core/tool_registry.py` | Tool registry | ~60 |
| `core/memory_manager.py` | Session memory | ~90 |
| `core/agent_store.py` | Agent CRUD | ~80 |
| `core/auto_agent_factory.py` | Dynamic agents | ~120 |
| `core/sub_agents.py` | Parallel execution | ~35 |
| `core/config.py` | Configuration | ~70 |
| `skills/*/skill.py` | Skill implementations | ~50-200 each |
| `tools/*.py` | Tool implementations | ~30-100 each |
| `web/static/*.html` | Frontend | ~100-150 each |

---

## 12. Deployment Checklist

- [ ] Set `KIMI_API_KEY` (or `OPENROUTER_API_KEY` as fallback)
- [ ] Configure `config/agent.json` with model settings
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run tests: `pytest tests/ -v`
- [ ] Start server: `python -m uvicorn web.server:app --host 0.0.0.0 --port 8000`
- [ ] Open `http://localhost:8000`
- [ ] Test chat with "Hello"

---

**For questions or issues:** Check `plans/my-agent-web-ui.md` for detailed architecture decisions.

**Next steps for development:** See ARCHITECTURE.md for detailed component interactions.
