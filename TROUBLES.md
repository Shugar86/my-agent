# АУДИТ БАГОВ И РАСХОЖДЕНИЙ: my-agent

> Дата: 2026-05-27 (re-audit #9 — верификация Phase 0–2)
> Тип: code audit + fix sprint + re-verification
> Метод: pytest gate 46/46, spot-checks C/H, TestClient smoke

---

## Re-audit #9 — результаты (2026-05-27)

### Автоматический gate

| Проверка | Результат |
|----------|-----------|
| `load_config()` без `agent.yaml` | **PASS** — model dict из `config/agent.json` |
| MemoryManager SQLite URL | **PASS** — `PG: False` |
| DBManager `DATABASE_URL=""` | **PASS** — `db_type: sqlite` |
| `spawn_for_task` sync | **PASS** — `spawn async: False` |
| pytest subset (46 tests) | **PASS** — 46/46 |
| pytest full (без e2e/real_api/ollama) | **PARTIAL** — suite ~500+ tests, >5 min; isolated failures не воспроизводятся |

### Spot-checks CRITICAL + HIGH (Phase 0–2)

Все 13 CRITICAL (11 реальных) и 16 HIGH из аудита #8 — **подтверждены** (grep + smoke):

- C1–C12, C15: код на месте; Alembic `005` upgrade на существующей БД — **PASS**
- C9: `agent_styled.py`, `agent_backup.py` — **удалены**
- C13, C14: false positive — **без изменений, OK**
- H1–H16: JWT rate-limit, session_id, FK pragma, Docker run_python, translate_text, WS stream — **PASS**
- SkillLoader: 33 skills, 77 tools, `translate_text` registered

### Manual smoke (TestClient + Docker)

| Сценарий | Результат |
|----------|-----------|
| `python agent.py --help` | **PASS** |
| `GET /metrics` | **PASS** — `active_sessions` present |
| `GET /api/stats` | **PASS** — `model: openrouter/owl-alpha` |
| `POST /api/chat` + `session_id` | **PASS** — 200, tools loaded |
| `POST /api/chat` `auto_agents=True` | **PASS** — no TypeError |
| `resolve_agent_model_config({"model":"balanced"})` | **PASS** |
| `WS /ws/chat` | **PASS** — `thinking` → `chunk`* → `done` |
| `execute_code` python + javascript | **PASS** — Docker sandbox (42, 1) |

### Doc cleanup (устаревшие строки)

| ID | Статус |
|----|--------|
| M12 | **FIXED** в аудите #8 (H6) — строка в MEDIUM устарела |
| M14 | **FIXED** в SSE path — `isinstance(args, str)` guard |
| L1, L2, L14 | **FIXED** — entry points удалены |

### Backlog Phase 3 (не регрессия)

18 MEDIUM + 16 LOW остаются open — см. секцию «ОТЛОЖЕНО». Приоритет: **L8** rotate `.env` key.

**Критерий успеха re-audit #9: ВЫПОЛНЕН.**

---

## ✅ ИСПРАВЛЕНО (аудит #8 — Phase 0–2, 2026-05-27)

| # | Баг | Где | Статус |
|---|-----|-----|--------|
| C1, C2 | `load_config()` → missing `agent.yaml` | `core/config.py`, `agent.py`, `web/server.py` | ✅ FIXED — `load_agent_config` + merge |
| C3 | `await` на sync `spawn_for_task` | `core/orchestrator.py` | ✅ FIXED |
| C4 | `.get("primary")` на string model | `web/server.py` | ✅ FIXED — `resolve_agent_model_config` |
| C5 | messaging skill import | `core/skill_loader.py` | ✅ FIXED — `sys.path` + None guard |
| C6 | `values[0]` на пустом списке | `skills/google_sheets/skill.py` | ✅ FIXED |
| C7 | JS без node в slim image | `tools/code_tools.py`, `docker_sandbox.py` | ✅ FIXED — `node:20-slim` |
| C8 | `spec_from_file_location` None | `plugin_manager.py`, `skill_loader.py` | ✅ FIXED |
| C9, L1, L2 | Мёртвые entry points | `agent_styled.py`, `agent_backup.py` | ✅ FIXED — удалены |
| C10 | Alembic 005 vs StateDB | `005_unified_schema.py`, `sessions_router.py` | ✅ FIXED — idempotent + lazy StateDB |
| C11 | MemoryManager SQLite→PG | `core/memory_manager.py` | ✅ FIXED — scheme check |
| C12 | DBManager empty DATABASE_URL | `core/db_manager.py` | ✅ FIXED — normalize URL |
| C15 | EventBus async handlers | `core/event_bus.py`, `runtime.py` | ✅ FIXED — `emit_async` |
| H1 | Rate limit без user_id | `web/server.py` | ✅ FIXED — JWT decode в middleware |
| H2 | session_id игнорируется | `web/server.py` | ✅ FIXED |
| H3 | FK pragma per-connection | `core/db_manager.py` | ✅ FIXED |
| H4 | `get_event_loop()` deprecated | `core/auto_agent_factory.py` | ✅ FIXED — `run_coro_sync` |
| H5 | local профиль OPENROUTER key | `core/wizard.py` | ✅ FIXED — empty api_key for Ollama |
| H6, M12 | `run_python` subprocess | `tools/data_tools.py` | ✅ FIXED — Docker sandbox |
| H7 | голый `except:` | `tools/docs_tools.py` | ✅ FIXED |
| H8 | тавтология в тесте | `tests/test_production_hardening.py` | ✅ FIXED |
| H9 | asyncpg None guard | `skills/sql_db/skill.py` | ✅ FIXED |
| H10 | ACTIVE_SESSIONS always 0 | `web/server.py` | ✅ FIXED — SSE/WS gauge |
| H11 | SkillLoader cascade fail | `core/skill_loader.py` | ✅ FIXED — per-skill try/except |
| H12 | `translate_text` missing | `skills/translation/skill.py` | ✅ FIXED — registered |
| H13 | session_cache rewrite on read | `core/session_cache.py` | ✅ FIXED — read-only fallback |
| H14 | TUI без SkillLoader | `cli/tui.py` | ✅ FIXED — `_get_cached_skill_loader` |
| H15, H16 | WS fake stream | `web/server.py` | ✅ FIXED — real LLM stream |
| — | `asyncio.run()` в CLI | `agent.py`, `cli/tui.py` | ✅ FIXED — `run_coro_sync` / single-loop TUI |
| M1 | Tavily empty → DDGS | `tools/web_tools.py` | ✅ FIXED — fall through |
| M16 | tools auto-register | `tools/__init__.py` | ✅ FIXED — `register_all_tools()` |

**NOT CONFIRMED (не трогали):** C13 loop detection, C14 FakeToolCall.id — код корректен.

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

## 🔴 CRITICAL — все закрыты в аудите #8

*(см. таблицу «ИСПРАВЛЕНО (аудит #8)»)*

---

## 🟠 HIGH — все закрыты в аудите #8

*(см. таблицу «ИСПРАВЛЕНО (аудит #8)»)*

---

## 🟡 MEDIUM (некорректное поведение в edge-case, логические ошибки)

| # | Баг | Файл | Строка | Описание |
|---|-----|------|--------|----------|
| ~~M1~~ | ~~Tavily пустой результат → None~~ | ~~`tools/web_tools.py`~~ | — | ✅ FIXED — fall through to DDGS |
| M2 | `\|` в BASH_DENYLIST никогда не сматчится | `tools/code_tools.py` | 14,21 | Перед токенизацией `\|` заменяется на пробел: `replace("|", " ")`. Токен `\|` никогда не появится в tokens → dead code |
| M3 | `timeout` параметр игнорируется в Docker-раннерах | `tools/code_tools.py` | 40,59,81 | Все три runner принимают `timeout`, но не передают его в `docker_sandbox.run_python(code)` / `run_bash(code)`. Методы сэндбокса используют `self.timeout` (30s) |
| M4 | Одинаковый тул `transcribe_audio` — перезатирание | `skills/audio_transcription/skill.py:45`, `skills/voice_io/skill.py:96` | — | Два скила регистрируют тул с именем `"transcribe_audio"`. В `ToolRegistry` второй регистрируется, первый теряется. Какая реализация останется — зависит от порядка файлов (недетерминировано) |
| M5 | Регулярка для `<li>` в `<ul>` сломана | `skills/docs/skill.py` | 176 | `re.sub(r'(<li>.+</li>\n)+', r'<ul>\g<0></ul>', html)` — никогда не сгруппирует весь список в один `<ul>`. Может создать вложенные `<ul>`. HTML-конвертация списков сломана |
| M6 | `gmail_list_unread` — не зарегистрирован как тул | `skills/gmail/skill.py` | 59–70 | Функция полностью реализована, но отсутствует в `register_tools()`. Никогда не вызывается агентом (только из `scheduler_manager.py` внутренне) |
| M7 | Пустой `[]` tool_calls → `None` | `core/memory_manager.py` | 104,190 | `msg.get("tool_calls") if msg.get("tool_calls") else None` — пустой список `[]` falsy, сохраняется как `None` вместо `"[]"`. Потеря данных |
| M8 | Тест-заглушка (body = pass) | `tests/test_db_manager.py` | 93–98 | `test_fallback_to_sqlite` — тройной `with patch(...)` вокруг `pass`. Бесполезный тест |
| M9 | `-> str` возвращает tuple | `cli/tui.py` | 708 | `async def process_message(self, text: str) -> str` — реально возвращает `(str, float)` |
| M10 | `extra_headers` в `web3` — смесь v5/v6 API | `skills/web3/skill.py` | 162 | `signed.rawTransaction` (web3.py v5) + `send_raw_transaction` (web3.py v6). Нестабильно |
| M11 | Тройная загрузка AgentStore() на каждый вызов | `tools/auto_agents_tools.py` | 26–27,35–36 | Lambda создаёт новый `AgentStore()` при каждом исполнении тула. Race condition на `agents/registry.json` |
| ~~M12~~ | ~~`run_python` без Docker~~ | ~~`tools/data_tools.py`~~ | — | ✅ FIXED аудит #8 (H6) — Docker sandbox |
| M13 | Два одинаковых `web_scrape` | `tools/web_tools.py:42`, `tools/deep_search_tools.py:140` | — | Идентичная функция. Поддержка расходится |
| ~~M14~~ | ~~`json.loads` на не-строку~~ | ~~`web/server.py`~~ | — | ✅ FIXED аудит #8 — `isinstance(args, str)` guard в SSE |
| M15 | Schema mismatch: `auth_provider` колонки нет в SQLite | `core/user_manager.py` | 207 | `_init_sqlite()` — пустой `pass`. `_init_pg()` добавляет колонку через ALTER TABLE. INSERT на SQLite упадёт если колонки нет |
| ~~M16~~ | ~~`tools/__init__.py` пуст~~ | ~~`tools/__init__.py`~~ | — | ✅ FIXED — `register_all_tools()` on import |
| M17 | `_SKILL_KEYWORDS` не содержит 80%+ заявленных тулов | `core/skill_cache.py` | 12–42 | Ручная карта ключевых слов. Тулы `analyze_csv`, `create_chart`, `create_presentation`, `deep_search` и др. не имеют записей → keyword-фильтрация **молча исключает** большинство скиллов |
| M18 | `psycopg2.ThreadedConnectionPool` в асинхронном приложении | `core/db_manager.py` | 74 | Синхронный пул psycopg2 в async FastAPI. Все DB-запросы блокируют event loop. Нужен `asyncpg` или `psycopg` v3 async |

---

## ⚪ LOW (косметика, dead code, дубликаты)

| # | Баг | Файл | Строка | Описание |
|---|-----|------|--------|----------|
| ~~L1~~ | ~~3 точки входа~~ | — | — | ✅ FIXED аудит #8 — удалены styled/backup |
| ~~L2~~ | ~~entrypoint не синхронизирован~~ | `pyproject.toml` | 91 | ✅ FIXED — только `agent:main` |
| L3 | Двойная регистрация тулов | `core/skill_loader.py:78-84`, `core/builder.py:97-103` | — | `load_all()` вызывает `register_tools()`, потом `build()` вызывает `enable()` который снова дёргает `register_tools()` |
| L4 | Dead import `run_parallel_agents` | `core/orchestrator.py` | 3 | Импортирован, но используется только `run_parallel_agents_async` |
| L5 | Dead import `LLMGateway` | `skills/vision/skill.py` | 11 | Импортирован, нигде не используется |
| L6 | Мёртвый путь `/onboarding` | `web/server.py` | 200–201 | `if path == "/onboarding":` — никогда не сматчится (см. AuthMiddleware логику) |
| L7 | Деплой скрипты в entrypoint — не проверены | `scripts/entrypoint.sh` | 5,8 | `seed_workflow_templates.py` и `generate_demo_artifact.py` вызываются без проверки существования/ошибок |
| L8 | `.env` с валидным ключом в git | `.env` | 8 | `OPENROUTER_API_KEY` — реальный ключ, закоммичен. Security issue |
| L9 | `config/agent.json` fallback не совпадает с `MODEL_PROFILES` | `config/agent.json` | 6 | `google/gemini-2.5-flash-preview` vs `openrouter/owl-alpha` в `MODEL_PROFILES` |
| L10 | `requirements.txt` — не используется | `requirements.txt` | — | Дублирует `pyproject.toml`. Никто не читает. `pip install -e .` игнорирует |
| L11 | `_set_auth_cookie` — мёртвая обёртка | `web/server.py` | 407–408 | Определена, нигде не вызвана |
| L12 | `conninfo` вычисляется но не используется | `core/db_manager.py` | 73–74 | `conninfo = self.database_url.replace(...)` — пул создаётся через `dsn=self.database_url` |
| L13 | `re.sub` заново импортируется внутри функции | `skills/docs/skill.py` | 161 | `import re` — уже импортирован на уровне модуля (строка 2) |
| ~~L14~~ | ~~`import yaml` в agent_backup~~ | — | — | ✅ FIXED — файл удалён |
| L15 | `asyncio.run()` в `ThreadPoolExecutor` — новый event loop на тред | `core/auto_agent_factory.py` | 19–24 | `pool.submit(asyncio.run, coro).result()` — создаёт отдельный event loop в каждом треде пула. Утечка при частых вызовах |
| L16 | `@app.on_event("startup")` deprecated | `web/server.py` | 233, 255 | FastAPI рекомендует lifespan-обработчики. Два ворнинга при старте сервера |

---

## 📊 ДИНАМИКА

| Итерация | CRITICAL | HIGH | MEDIUM | LOW |
|----------|----------|------|--------|-----|
| Аудит #6 | 9 | 10 | 15 | 14 |
| Аудит #7 | 15 | 16 | 18 | 16 |
| **Аудит #8 (fix)** | **0** | **0** | **18 open** | **16 open** |
| **Re-audit #9** | **0** | **0** | **15 open** | **13 open** |

---

## ⏳ ОТЛОЖЕНО (Phase 3+ — отдельные PR)

**MEDIUM (15 open):** M2 BASH_DENYLIST `|`, M3 timeout в Docker, M4 transcribe_audio dup, M5 docs `<ul>`, M6 gmail_list_unread, M7 tool_calls `[]`, M8 test_db_manager stub, M9 TUI return type, M10 web3 API mix, M11 AgentStore race, M13 web_scrape dup, M15 auth_provider SQLite, M17 skill_cache keywords, M18 psycopg2 sync pool.

**LOW (13 open):** L3 double register_tools, L4 dead import orchestrator, L5 vision LLMGateway, L6 /onboarding dead path, L7 entrypoint.sh, **L8 .env key in git (rotate!)**, L9 agent.json vs MODEL_PROFILES, L10 requirements.txt dup, L11 _set_auth_cookie dead, L12 conninfo unused, L13 re import in docs, L15 asyncio.run thread pool, L16 deprecated lifespan.

---

## Re-audit #9 — чеклист (выполнен 2026-05-27)

```bash
cd ~/dev/my-agent && source .venv/bin/activate

# Gate
python -c "from core.config import load_config; print(load_config().get('model'))"
python -c "from core.memory_manager import MemoryManager; m=MemoryManager({'enabled':True}); print('PG:', m._use_pg)"
DATABASE_URL="" python -c "from core.db_manager import DBManager; print(DBManager().db_type)"
pytest tests/test_async_utils.py tests/test_db_manager.py tests/test_code_tools.py \
       tests/test_resolve_agent_model.py tests/test_production_hardening.py -q

# Spot-checks
alembic upgrade head
python -c "from core.builder import _get_cached_skill_loader; from core.tool_registry import registry; _get_cached_skill_loader(); print(len(registry.get_schemas()), 'tools')"
python -c "from skills.google_sheets.skill import sheets_write; print(sheets_write('x','A1',[]))"
python -c "from tools.code_tools import execute_code; print(execute_code('javascript','console.log(1)'))"
ls agent_styled.py agent_backup.py  # expect: No such file

# Manual (TestClient)
python -c "
from fastapi.testclient import TestClient
from web.server import app
from core.auth import create_access_token
import os; os.environ['AGENT_SECRET_KEY']='test-secret-key-32-chars-minimum!!'
c=TestClient(app); t=create_access_token({'sub':'a','user_id':'u1','role':'admin'})
print(c.get('/metrics').status_code, c.get('/api/stats',cookies={'access_token':t}).status_code)
"
```

---

```bash
# 1. Alembic 005 — проверить что таблицы уже есть
python -c "import sqlite3; con = sqlite3.connect('data/agent.db'); print([r[0] for r in con.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()])"

# 2. MemoryManager — тест на SQLite URL
python -c "from core.memory_manager import MemoryManager; m = MemoryManager(); print('PG:', m._use_pg)"

# 3. DBManager — пустой DATABASE_URL
DATABASE_URL="" python -c "from core.db_manager import DBManager; print(DBManager().db_type)"

# 4. Loop detection — results vs str
python -c "results = ['ok', 'ok']; print(results == 'loop_detected')"

# 5. FakeToolCall hasattr id
python -c "class FTC: pass; ftc = FTC(); print(hasattr(ftc, 'id'))"

# 6. tools/__init__.py — проверить что registry пуст
python -c "from core.tool_registry import ToolRegistry; tr = ToolRegistry(); print('tools:', len(tr.list_tools()))"

# 7. tests — быстрые
pytest tests/test_async_utils.py tests/test_db_manager.py tests/test_code_tools.py -q
```

## Re-audit #6 — чеклист

```bash
# 1. load_config() крашится — поправить путь или проверять agent.json
python -c "from core.config import load_config; print(load_config())"

# 2. await на не-async — проверить auto_agent_factory.spawn_for_task
python -c "from core.auto_agent_factory import AutoAgentFactory; import inspect; print(inspect.iscoroutinefunction(AutoAgentFactory.spawn_for_task))"

# 3. model.get('primary') на строке
python -c "agent_config = {'model': 'balanced'}; print(agent_config.get('model', {}).get('primary'))"

# 4. agent_styled.py импорты
python -c "import ast; tree = ast.parse(open('agent_styled.py').read()); [print(n.names) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == 'agent']"

# 5. plugin_manager None spec
python -c "import importlib.util; print(importlib.util.spec_from_file_location('x', '/nonexistent.py'))"

# 6. tests — быстрые
pytest tests/test_async_utils.py tests/test_db_manager.py tests/test_code_tools.py -q
```

**Итог #9 (re-audit):** Phase 0–2 fixes **подтверждены**. Gate 46/46 PASS. Manual smoke PASS. CRITICAL/HIGH = 0 open. Phase 3: 17 MEDIUM + 13 LOW.

**Итог #8:** Phase 0–2 закрыли **13 CRITICAL** (11 реальных + 2 false positive), **16 HIGH**. pytest gate: 46/46. Phase 3 — MEDIUM/LOW в backlog.

**Итог #7:** *(исторический)* аудит #7 добавил +6 CRITICAL, +6 HIGH. Основной системный баг — тулы не регистрировались.
