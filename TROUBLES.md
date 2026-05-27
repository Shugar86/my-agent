# АУДИТ БАГОВ И РАСХОЖДЕНИЙ: my-agent

> Дата: 2026-05-27 (аудит #5 — CRITICAL+HIGH fix + re-audit)
> Тип: code audit (как есть, по реальному коду)

---

## ✅ ИСПРАВЛЕНО (аудиты #2–#5)

| # | Баг | Где | Статус |
|---|-----|-----|--------|
| 1–7 | RCE, Playwright, slides, code_tools, Caddy, cryptography | см. аудит #2–#3 | ✅ FIXED |
| 1, 38 | MCP async tools + kwargs | `tool_registry`, `mcp_manager` | ✅ FIXED — `async_utils.invoke_execute_fn` |
| 2, 10, 11 | Scheduler `run_until_complete` | `skills/scheduler/skill.py` | ✅ FIXED — `run_coro_sync` |
| 16 | Stale MCP session closure | `mcp_manager.py` | ✅ FIXED — `server_handle.session` |
| 19 | `setup_date` = Path.home() | `wizard.py` | ✅ FIXED — ISO UTC |
| 20 | MCP Client stdio blocks loop | `mcp_client_manager.py` | ✅ FIXED — `asyncio.to_thread` |
| 21 | MCP client proxy `run_until_complete` | `mcp_client_manager.py` | ✅ FIXED — `run_coro_sync` |
| 22 | `asyncio.run` from async | `sub_agents.py` | ✅ FIXED |
| 23 | `StateDB()` at import | `session_cache.py` | ✅ FIXED — lazy singleton |
| 24 | ContextCompressor bypasses gateway | `context_compressor.py`, `runtime.py` | ✅ FIXED — `llm.chat` + `compress_async` |
| 25 | `INSERT OR REPLACE` on PG | `workflow/store.py` | ✅ FIXED — `ON CONFLICT` |
| 26 | `json_extract` on PG | `usage/tracker.py` | ✅ FIXED — `->>'workflow_id'` |
| 3 | A2A delivered audit | `a2a_server.py` | ✅ FIXED — Redis `a2a:delivered:{id}` |
| 4 | A2A TTL dead code | `a2a_server.py` | ✅ FIXED — `expires_at` |
| 5 | `datetime.utcnow()` | a2a, scheduler, feedback | ✅ FIXED — `timezone.utc` |
| 6 | `recover_stale_jobs` race | `run_queue.py`, `redis_client.py` | ✅ FIXED — atomic `rpoplpush` |
| 7 | `datetime('now')` on PG | `workflow/state.py` | ✅ FIXED — dual SQL |
| 17 | A2A broadcast race | `a2a_server.py` | ✅ FIXED — per-agent fan-out |
| 27 | Sync migrations in startup | `web/server.py` | ✅ FIXED — `asyncio.to_thread` |
| 28 | feedback `_ensure_table` no-op | `feedback.py` | ✅ FIXED — `CREATE TABLE IF NOT EXISTS` |
| 29 | `scheduled_jobs_log` без таблицы | `scheduler_manager.py` | ✅ FIXED — guard + `_log_scheduled_job` |
| 30 | LLM fallback kwargs stale | `llm_gateway.py` | ✅ FIXED — `_build_kwargs(model=fallback)` |
| 31 | API keys on stderr (CLI) | `agent.py`, `logger.py` | ✅ FIXED — `RedactingFormatter` |
| 18 | GitHub MCP env | `mcp_clients.json` | ✅ OK — `${GITHUB_TOKEN}` mapping |
| 44 | `core/models.py` missing | alembic | ✅ OK — файл существует |

**#32 action nodes:** lazy import уже в `workflow/nodes/action.py` (импорт внутри handler).

---

## 🔴 CRITICAL — открытых нет

---

## 🟠 HIGH — отложено / documented

| # | Баг | Примечание |
|---|-----|------------|
| 33 | MCP HTTP SSE не читается | Documented limitation; HTTP MCP не в prod path |
| 34 | MCP resources/prompts unused | Low priority; discovery only |

---

## 🟡 MEDIUM (не в scope аудита #5)

| # | Баг | Файл |
|---|-----|------|
| 8 | Redis rate limiter fixed window | `redis_client.py` |
| 9 | EventBus без async handlers | `event_bus.py` |
| 12 | Silent `except Exception: pass` | session_cache, state_db, mcp_server |
| 35 | `consume()` до threshold check | `iteration_budget.py` |
| 36 | `save_messages` без одной транзакции | `state_db.py` |
| 37 | `save_session` дублирует сообщения | `memory_manager.py` |
| 39 | `_max_tokens` getattr fallback | `builder.py` |
| 40 | Tavily в `run_api_test.py` без ключа | `run_api_test.py` |

---

## ⚪ LOW (не в scope)

13 AuthMiddleware tautology, 14 CORS :8000, 15 translate stub, 41 `get_event_loop`, 42 conninfo dead code, 43 models.yaml, 45 StaticFiles path, 46 FastAPI в core/permissions.

---

## 📊 ДИНАМИКА

| Итерация | CRITICAL | HIGH | MEDIUM | LOW |
|----------|----------|------|--------|-----|
| Аудит #3 | 2 | 4 | 6 | 6 |
| Аудит #4 | +9 | +7 | +6 | +6 |
| **Аудит #5** | **0** | **2 doc** | 8 open | 8 open |

---

## Re-audit #5 — чеклист

```bash
# Должно быть 0:
rg 'datetime\.utcnow' my-agent --glob '*.py'

# Тесты:
pytest tests/test_async_utils.py tests/test_troubles_regression.py \
  tests/test_a2a_queue.py tests/test_run_queue_recovery.py \
  tests/test_llm_gateway_fallback.py tests/test_logging_redaction.py -q
```

**Итог:** MCP, scheduler, A2A, PG paths, startup migrations и logging — исправлены. MEDIUM/LOW — следующая итерация.
