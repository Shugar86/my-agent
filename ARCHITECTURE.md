# Architecture

> My Agent — System Architecture  
> Version: **3.5.2**

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser / CLI (agent.py)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE / WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI (web/server.py)                                     │
│  AuthMiddleware · rate limits · routers (workflow, teams, …) │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────┐   ┌──────────────┐   ┌──────────────────┐
│ Orchestrator│   │ Workflow     │   │ Billing / Usage  │
│ + AutoAgent │   │ Engine       │   │ Teams / Auth     │
│   Factory   │   │ (DAG executor│   │                  │
└──────┬──────┘   │  Redis queue)│   └──────────────────┘
       │          └──────┬───────┘
       ▼                 │
┌─────────────────────────────────────────────────────────────┐
│  AgentBuilder → AgentRuntime → LLMGateway (OpenRouter + litellm)│
│  SkillLoader · ToolRegistry · MemoryManager                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  skills/* · tools/* · agents/registry.json                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              PostgreSQL · Redis · ChromaDB (RAG)
```

---

## Frontend

React 18 SPA (`web/frontend/`), собирается в `web/static/app/`.

| Зона | Маршруты | Auth |
|------|----------|------|
| Public | `/`, `/demo`, `/showcase` | Нет |
| Product | `/app/*` | JWT cookie |
| Auth | `/login` | — |

Legacy static HTML в `website/` и `web/static/*.html` не используются для основного UI (кроме `login.html` при необходимости).

---

## Core execution

### AgentBuilder (`core/builder.py`)

Fluent configuration → `AgentRuntime`. Загружает skills, создаёт `LLMGateway`, memory, events.

### AgentRuntime (`core/runtime.py`)

Цикл до 20 turns: LLM → tool calls → results → сжатие контекста при переполнении.

### Orchestrator (`core/orchestrator.py`)

- **Handoff** — один агент
- **Parallel delegate** — `sub_agents` через ThreadPoolExecutor

### AutoAgentFactory (`core/auto_agent_factory.py`)

LLM планирует sub-agents → временные профили → parallel run → cleanup.

---

## Workflow engine

```
web/workflow_router.py
    → core/workflow/store.py      (persistence)
    → core/workflow/registry.py   (node types)
    → core/workflow/executor.py   (DAG run)
    → core/workflow/run_queue.py  (Redis RPOPLPUSH)
```

Узлы: `trigger.*`, `agent.skill`, `condition`, `action.webhook`, `action.n8n_webhook`, …

Runs async по умолчанию; sync с `{"wait": true}`.

---

## Data stores

| Store | Usage |
|-------|--------|
| PostgreSQL | Users, workflows, templates, billing |
| Redis | Sessions blacklist, rate limits, run queue |
| JSON files | Dev memory sessions (`memory/sessions/`) |
| ChromaDB | RAG knowledge base |

При `ENV=production` SQLite для основных данных не используется.

---

## Security (current)

| Layer | Implementation |
|-------|----------------|
| Auth | JWT httpOnly cookie, Google OAuth |
| Public paths | `web/security.py` → `is_public_path()` |
| Rate limit | Redis sliding window + slowapi |
| Code exec | Docker sandbox (`core/docker_sandbox.py`) |
| Self-modify | `self_dev` blocked in production |

См. [SECURITY.md](SECURITY.md).

---

## Module map

```
web/server.py
├── core/orchestrator.py → core/builder.py → core/runtime.py
├── core/workflow/* 
├── core/auth.py, core/billing/*
├── core/kimi_provider.py, core/configurator.py (model profiles)
└── core/agent_store.py

skills/*/skill.py → tools/*.py
```

---

## Scaling notes

| Bottleneck | Mitigation |
|------------|------------|
| Sync LLM in async routes | `asyncio.to_thread`, streaming |
| Skill load per build | Skill cache (`core/skill_cache.py`) |
| Single uvicorn worker | Multiple workers + shared Redis/PostgreSQL |
| Session JSON files | PostgreSQL + Redis in prod |

---

## Design patterns

| Pattern | Location |
|---------|----------|
| Builder | `core/builder.py` |
| Factory | `core/auto_agent_factory.py` |
| Strategy | `core/orchestrator.py` |
| Adapter | `core/llm_gateway.py`, `core/kimi_provider.py` |
| Plugin | `core/skill_loader.py` |
| Repository | `core/memory_manager.py`, workflow store |

---

Деплой и порты: [DEPLOYMENT.md](DEPLOYMENT.md), [SERVER.md](SERVER.md).
