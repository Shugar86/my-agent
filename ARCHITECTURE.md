# Architecture

> My Agent — System Architecture
> Version: 1.0.0

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                 │
│                   (Browser / CLI)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND                                │
│              (Vanilla HTML/CSS/JS)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dashboard │  │  Chat    │  │ Agents   │  │Settings  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP / SSE
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND                                │
│                   (FastAPI / Uvicorn)                         │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Router    │  │  API Layer   │  │  Middleware  │      │
│  │  (server.py)│  │  (models)    │  │ (handlers)   │      │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                │                 │              │
│         └────────────────┬┴─────────────────┘              │
│                          │                                 │
│                          ▼                                 │
│  ┌────────────────────────────────────────────────────┐   │
│  │              ORCHESTRATOR LAYER                      │   │
│  │                                                      │   │
│  │  ┌──────────────────┐  ┌──────────────────────┐     │   │
│  │  │   Orchestrator   │  │  AutoAgentFactory    │     │   │
│  │  │   (orchestrator) │  │  (auto_agent_factory)│     │   │
│  │  │                  │  │                      │     │   │
│  │  │  ┌────────────┐  │  │  ┌──────────────┐  │     │   │
│  │  │  │  Handoff   │  │  │  │Analyze Task  │  │     │   │
│  │  │  │  (single)  │  │  │  └──────────────┘  │     │   │
│  │  │  └────────────┘  │  │        │           │     │   │
│  │  │  ┌────────────┐  │  │        ▼           │     │   │
│  │  │  │  Parallel  │  │  │  ┌──────────────┐  │     │   │
│  │  │  │  Delegate  │──┼──┼──►│Spawn Agents  │  │     │   │
│  │  │  └────────────┘  │  │  └──────────────┘  │     │   │
│  │  └──────────────────┘  └──────────────────────┘     │   │
│  └──────────────────────────┬──────────────────────────┘   │
│                             │                              │
└─────────────────────────────┼──────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   AGENT EXECUTION LAYER                     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AgentBuilder (Builder Pattern)            │  │
│  │                                                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐           │  │
│  │  │ set_model│ │ set_role │ │set_skills│ ...        │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘           │  │
│  │       └──────────────┴──────────┘                    │  │
│  │                    │                                 │  │
│  │                    ▼                                 │  │
│  │              ┌──────────┐                           │  │
│  │              │  build()  │                           │  │
│  │              └────┬─────┘                           │  │
│  │                   │                                  │  │
│  │                   ▼                                  │  │
│  │         ┌──────────────────┐                        │  │
│  │         │  AgentRuntime    │                        │  │
│  │         │  (runtime.py)    │                        │  │
│  │         └────────┬─────────┘                        │  │
│  │                  │                                   │  │
│  │                  ▼                                   │  │
│  │         ┌──────────────────┐                        │  │
│  │         │     run()      │  ──► LLM Gateway       │  │
│  │         │   (20 turns)   │      (litellm)          │  │
│  │         └──────────────────┘                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  SUPPORTING MODULES                         │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │SkillLoader │  │ToolRegistry│  │MemoryManager│           │
│  │ (skills)   │  │  (tools)   │  │ (sessions)  │           │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ EventBus   │  │PluginManager│ │ContextCompressor│      │
│  │  (events)  │  │ (plugins)  │  │(compression) │         │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │AgentStore  │  │ Config     │  │ Logger     │            │
│  │ (registry) │  │ (settings) │  │ (logs)     │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. AgentBuilder (`core/builder.py`)

**Pattern:** Fluent Builder

**Responsibilities:**
- Configure model (primary, fallback, API key)
- Set role (system prompt)
- Load and enable skills
- Initialize memory, events, compression, plugins

**Flow:**
```
set_model() → set_role() → set_skills() → set_tools() → set_memory()
    → enable_events() → enable_compression() → enable_plugins()
    → build() → AgentRuntime
```

**Build Process:**
1. Create LLMGateway
2. Load ALL skills from disk
3. Enable only requested skills
4. Create MemoryManager
5. Create EventBus (if enabled)
6. Create ContextCompressor (if enabled)
7. Create PluginManager (if enabled)
8. Return AgentRuntime

**Issue:** Skills loaded on every build → disk I/O bottleneck

---

### 2. AgentRuntime (`core/runtime.py`)

**Pattern:** State Machine (while loop)

**Responsibilities:**
- Main execution loop (max 20 turns)
- Tool call handling
- Context compression when needed
- Memory persistence

**Algorithm:**
```python
while turn < max_turns:
    # Check if context needs compression
    if compressor.needs_compression(messages):
        messages = compressor.compress(messages)
    
    # Call LLM
    response = llm.chat(messages, tools=tools)
    
    # Handle tool calls
    if response.has_tool_calls:
        for tool_call in response.tool_calls:
            result = skills.execute_tool(tool_call.name, **args)
            messages.add_tool_result(tool_call.id, result)
        continue  # Next turn
    
    # Return final response
    return response.content
```

**States:**
1. `INIT` — Build system prompt
2. `LLM_CALL` — Send to LLM
3. `TOOL_CALL` — Execute tools
4. `TOOL_RESULT` — Add results to context
5. `RESPONSE` — Return to user

**Issue:** Blocking execution, no async support

---

### 3. Orchestrator (`core/orchestrator.py`)

**Pattern:** Strategy Pattern

**Responsibilities:**
- Route tasks to appropriate agents
- Handle single vs parallel execution
- Synthesize results from multiple agents

**Strategies:**

#### 3.1 Handoff (Single Agent)
```
User Request → Agent Config → Builder.build() → Agent.run() → Response
```

Used when:
- No sub_agents defined
- Simple task

#### 3.2 Parallel Delegate
```
User Request → Agent Config → Sub-Agent Configs
    ├── Sub-Agent 1 (Thread 1) → Result 1
    ├── Sub-Agent 2 (Thread 2) → Result 2
    └── Sub-Agent N (Thread N) → Result N
    
→ Synthesize Results → Combined Response
```

Used when:
- Agent has `sub_agents` list
- Complex task requiring multiple perspectives

**Implementation:**
```python
with ThreadPoolExecutor(max_workers=len(sub_agents)) as executor:
    futures = {executor.submit(agent.run, request): agent_id 
               for agent_id, agent in sub_agents.items()}
    
    for future in as_completed(futures):
        results[futures[future]] = future.result()
```

**Synthesis:**
Simple concatenation with headers:
```markdown
### agent_1

Result 1...

---

### agent_2

Result 2...
```

**Issue:** No intelligent merging, just concatenation

---

### 4. AutoAgentFactory (`core/auto_agent_factory.py`)

**Pattern:** Factory Pattern + LLM Planning

**Responsibilities:**
- Analyze task with LLM
- Determine required sub-agents
- Create temporary agent configs
- Execute in parallel
- Synthesize results
- Cleanup temp agents

**Algorithm:**
```python
def spawn_for_task(task_description, parent_agent_id):
    # Step 1: Analyze task
    sub_agents = llm.analyze_task(task_description)
    # Returns: [{"name": "researcher", "role": "...", "skills": [...]}]
    
    # Step 2: Create temp configs
    temp_ids = []
    for sub_agent in sub_agents:
        config = create_temp_config(sub_agent, parent)
        temp_id = store.save_agent(config)
        temp_ids.append(temp_id)
    
    # Step 3: Execute in parallel
    results = {}
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(orchestrator.run, task, id): id 
                   for id in temp_ids}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    
    # Step 4: Cleanup
    for temp_id in temp_ids:
        store.delete_agent(temp_id)
    
    # Step 5: Synthesize
    return synthesize_results(results)
```

**Prompt for Analysis:**
```
Analyze this task and determine what sub-agents are needed.
Available skills: deep_research, research, parsing, template, 
                 code_analysis, code_execution, web_automation, 
                 api_integration

Return JSON array of sub-agent definitions.
```

---

### 5. LLM Gateway (`core/llm_gateway.py`)

**Pattern:** Adapter Pattern

**Responsibilities:**
- Abstract different LLM providers
- Handle API keys
- Fallback on failure
- Pass parameters (temperature, max_tokens)

**Flow:**
```python
llm = LLMGateway({
    "primary": "openrouter/deepseek/deepseek-v4-flash:free",
    "fallback": "openrouter/deepseek/deepseek-chat",
    "api_key": "sk-..."
})

response = llm.chat(
    messages=[{"role": "user", "content": "Hello"}],
    tools=[...]
)
```

**Error Handling:**
```python
try:
    response = litellm.completion(**kwargs)
except Exception as e:
    if self.fallback:
        kwargs["model"] = self.fallback
        response = litellm.completion(**kwargs)
    else:
        raise
```

**Issue:** Only 1 retry, no exponential backoff

---

### 6. Skill Loader (`core/skill_loader.py`)

**Pattern:** Plugin Discovery

**Responsibilities:**
- Scan skill directories
- Load skill modules
- Extract tool schemas
- Enable/disable skills

**Discovery:**
```python
SKILLS_DIRS = [
    "skills/",                          # Project skills
    os.path.expanduser("~/.agent/skills/"),  # User skills
]
```

**Loading:**
1. Find all subdirectories in `skills/`
2. Check for `SKILL.md` and `skill.py`
3. Import `skill.py`
4. Call `register_tools(tool_registry)`
5. Store skill metadata

**Tool Schema Extraction:**
```python
def get_tool_schema(func):
    # Extract from docstring
    # Extract from type hints
    # Return OpenAI-compatible JSON schema
```

---

### 7. Memory Manager (`core/memory_manager.py`)

**Pattern:** Session Repository

**Responsibilities:**
- Create/load sessions
- Add user/assistant/tool messages
- Persist to JSON files

**Storage:**
```
memory/
└── sessions/
    └── {session_id}.json
```

**Session Format:**
```json
{
  "id": "default",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"}
  ],
  "created_at": "2026-05-21T10:00:00",
  "updated_at": "2026-05-21T10:05:00"
}
```

**Scopes:**
- `task` — per request (default)
- `agent` — shared across requests to same agent
- `global` — shared across all agents

**Issue:** JSON files, no TTL, no cleanup

---

## Data Flow

### Chat Request Flow

```
User → Browser → POST /api/chat
    → server.py::chat_endpoint()
    → ChatRequest validation
    → Orchestrator.run(request.message, agent_id)
        → AgentStore.get_agent(agent_id)
        → If sub_agents: Parallel Delegate
            → ThreadPoolExecutor
            → Multiple AgentRuntime.run()
            → Synthesize results
        → Else: Handoff
            → AgentBuilder.build()
                → SkillLoader.load_all()
                → LLMGateway()
                → MemoryManager()
            → AgentRuntime.run(user_input)
                → LLM.chat(messages, tools)
                    → litellm.completion()
                        → OpenRouter API
                    ← Response
                ← If tool_calls:
                    → For each tool:
                        → ToolRegistry.execute()
                        → Skill.execute_tool()
                        ← Result
                    → Add to messages
                    → Next turn
                ← Else:
                    → Final response
            ← Return response
        ← Return result
    ← JSONResponse({"response": result})
← Browser displays result
```

---

## Module Dependencies

```
web/server.py
├── core/orchestrator.py
│   ├── core/builder.py
│   │   ├── core/llm_gateway.py
│   │   ├── core/skill_loader.py
│   │   │   └── tools/*.py
│   │   ├── core/memory_manager.py
│   │   ├── core/event_bus.py
│   │   ├── core/context_compressor.py
│   │   └── core/plugin_manager.py
│   ├── core/sub_agents.py
│   │   └── (same as builder chain)
│   └── core/agent_store.py
├── core/auto_agent_factory.py
│   ├── core/agent_store.py
│   ├── core/orchestrator.py
│   └── core/llm_gateway.py
└── core/config.py
```

---

## Design Patterns Used

| Pattern | File | Purpose |
|---------|------|---------|
| **Builder** | `core/builder.py` | Fluent agent configuration |
| **Factory** | `core/auto_agent_factory.py` | Dynamic agent creation |
| **Strategy** | `core/orchestrator.py` | Single vs parallel execution |
| **Adapter** | `core/llm_gateway.py` | Abstract LLM providers |
| **Plugin** | `core/skill_loader.py` | Dynamic skill loading |
| **Repository** | `core/memory_manager.py` | Session persistence |
| **Observer** | `core/event_bus.py` | Event-driven communication |
| **Decorator** | `core/context_compressor.py` | Add compression behavior |
| **Singleton** | (needs impl) | SkillLoader caching |

---

## Scaling Considerations

### Current (Single Node)
```
User → Uvicorn (1 worker) → Python process → Disk (JSON)
```

### Target (Multi-Node)
```
Users → Nginx → Uvicorn (4 workers) → Redis → PostgreSQL
                ↓
           Celery Workers
                ↓
           LLM API (OpenRouter)
```

### Bottlenecks
1. **Disk I/O** — JSON memory, skill loading
2. **CPU** — litellm sync calls block event loop
3. **Memory** — no cleanup of old sessions
4. **Network** — LLM API latency (~2-5s per call)

### Solutions
| Problem | Solution |
|---------|----------|
| Disk I/O | Redis for memory, cache skills in RAM |
| CPU blocking | Async runtime, asyncio.to_thread() |
| Memory growth | TTL on sessions, LRU cache |
| Network latency | Streaming responses, connection pooling |

---

## Security Considerations

### Current
- API key in `config/agent.json` (file permissions)
- No authentication on web UI
- No rate limiting
- No input validation beyond Pydantic

### Required
- OAuth2 / JWT authentication
- API key rotation
- Rate limiting per user
- Input sanitization
- Sandbox code execution
- HTTPS in production

---

End of Architecture Document
