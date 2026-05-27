# АУДИТ БАГОВ И РАСХОЖДЕНИЙ: my-agent

> Дата: 2026-05-27
> Тип: code audit (как есть, по реальному коду, без документации)

---

## 🔴 CRITICAL (15)

### 1. MCP `tools/call` полностью не работает — **RESOLVED**
- **web/mcp_server.py** — `_call_tool` использует `meta.get("execute")` (ключ из `ToolRegistry.register()`).

### 2. A2A очередь никогда не удаляет сообщения — **RESOLVED**
- **web/a2a_server.py** — `_dequeue_for_recipient` использует `queue_pop` (RPOP); memory fallback удаляет доставленные сообщения.

### 3. Шедулер импортирует несуществующий класс — **RESOLVED**
- **core/scheduler_manager.py** — вызывает `await agent.run()` напрямую, без `Runtime`.

### 4. Шедулер оборачивает уже собранного агента — **RESOLVED**
- См. #3 — двойная обёртка удалена.

### 5. StateDB: вызов несуществующих методов — **RESOLVED**
- **core/state_db.py** — `save_messages()` и `clear_session()` реализованы; `session_cache.py` вызывает их.

### 6. Loop detection — мёртвый код — **RESOLVED**
- **core/runtime.py:291** — проверка `results == "loop_detected"` (второй элемент tuple).

### 7. Caddyfile проксит на 8000, сервер на 8020 — **RESOLVED**
- **Caddyfile** — `reverse_proxy my-agent:8020`.

### 8. Missing dependency: `cryptography` не в `pyproject.toml` — **RESOLVED**
- **pyproject.toml** — добавлен `cryptography>=42.0.0`.

### 9. Dockerfile: Cryptography не установится — **RESOLVED**
- См. #8 — `pip install -e .` подтягивает прямую зависимость.

### 10. Несуществующий скрипт в setup.bat — **RESOLVED**
- **setup.bat** — пункт shortcut отключён с сообщением «not supported».

### 11. ORM/models.py не синхронизирован с БД — **RESOLVED (partial)**
- **core/models.py** — колонки миграций 003–004 добавлены; **alembic/env.py** — `include_object` блокирует autogenerate DROP для DB-only таблиц.

### 12. `eval()` на метаданных видео → RCE — **RESOLVED**
- **skills/video_processing/skill.py** — `Fraction()` вместо `eval()`.

### 13. `exec()` с полными builtins в data_analyst → RCE — **RESOLVED**
- **skills/data_analyst/skill.py** — `run_python_code()` удалён.

### 14. Browser skill — утечка страниц Playwright — **RESOLVED**
- **skills/browser/skill.py** — `_active_page` переиспользуется; предыдущая страница закрывается при `navigate()`.

### 15. slides_tools передаёт неправильный тип в export_to_pptx — **RESOLVED**
- **save_slide_html** пишет `deck.json`; **slides_tools.export_pptx** загружает deck из JSON.

---

## 🟠 HIGH (12)

### 16. A2A статус не персистится обратно в Redis
- **web/a2a_server.py:162-164** — `msg["status"] = "delivered"` меняет только локальный dict в HTTP-ответе. Статус в Redis не обновляется. Всегда `"pending"`.

### 17. Race condition в run_queue.recover_stale_jobs
- **core/workflow/run_queue.py:55-59** — `recover_stale_jobs` читает PROCESSING_KEY → пушит в PENDING_KEY → **DELETE PROCESSING_KEY**. Между push и delete конкурентный воркер может добавить новые элементы в PROCESSING_KEY — они будут **потеряны**.

### 18. Job silently lost при отказе Redis
- **core/workflow/run_queue.py:119-122** — Если `queue_remove` не удался (Redis временно недоступен), job остаётся в PROCESSING_KEY и **никогда не ретраится** (только при рестарте сервиса).

### 19. context_compressor bypassит LLMGateway (нет retry/fallback)
- **core/context_compressor.py:36** — `_summarize_sync` вызывает `litellm.completion()` напрямую, bypassя ретраи с backoff, fallback модель, error classification, и логирование LLMGateway. Транзиентная ошибка = fail immediately.

### 20. `run_until_complete` в async-контексте упадёт
- **core/mcp_client_manager.py:319** — `asyncio.get_event_loop().run_until_complete(...)` → `RuntimeError: This event loop is already running` при вызове MCP-клиента изнутри async-хода (а все вызовы инструментов именно такие).

### 21. Двойное управление схемой БД
- **db_manager.py:165-218** (`create_tables()`) vs **alembic/001_init.py** — `installed_skills`, `metrics`, `sessions` создаются в двух местах. Два источника истины — гарантированный schema drift.

### 22. CLI-сессии в отдельной SQLite
- **cli/tui.py:59** — `StateDB("data/cli_sessions.db")` — отдельная БД, не та, что у веба (`data/agent.db`). История чатов в CLI не видна в UI и наоборот. Фрагментация данных.

### 23. GitHub MCP client: несовпадение env vars
- **config/mcp_clients.json:19** — `GITHUB_PERSONAL_ACCESS_TOKEN`
- **.env.example:43** — `GITHUB_TOKEN`
- GitHub MCP-клиент никогда не получит ключ.

### 24. `_run_async` в scheduler skill падает в async-контексте
- **skills/scheduler/skill.py:6-14** — `loop.run_until_complete(coro)` на уже запущенном event loop → `RuntimeError`.

### 25. Shell injection в code_tools
- **tools/code_tools.py:62-63** — `code.replace("'", "'\"'\"'")` + `f"node -e '{escaped}'"` — хрупкое экранирование. Строка с `'"'"'` последовательностью пробивает оболочку. Использовать temp-файлы.

### 26. Postgres query crash если asyncpg не установлен
- **skills/sql_db/skill.py:32-49** — Если `asyncpg` не установлен (import failed → `None`), `await None.connect()` → `AttributeError`. Нет guard-проверки.

### 27. Двойной schema init в db_manager.create_tables vs Alembic
- **core/db_manager.py:165-218** — Создаёт 4 таблицы (`sessions`, `users`, `installed_skills`, `metrics`) через raw SQL. Это отдельный путь управления схемой, дублирующий Alembic.

---

## 🟡 MEDIUM (25)

### 28. Gauge метрики рассинхрон
- **web/server.py:186** — `ACTIVE_SESSIONS.inc()` без гарантированного `.dec()` на некоторых error path.

### 29. Циркулярный import в auth_router
- **web/auth_router.py:95** — `from web.server import user_manager` — ленивый импорт, создающий циклическую зависимость `server.py → auth_router.py → server.py`.

### 30. ThreadPoolExecutor внутри ThreadPoolExecutor
- **core/auto_agent_factory.py:19-21, 53** — Вложенные ThreadPoolExecutor'ы. Хаос с event loop.

### 31. MemoryManager дублирует все сообщения при каждом save
- **core/memory_manager.py:102-110** — `save_session` вызывает `add_message` для всех сообщений сессии каждый раз. Без дедупликации. История чата растёт квадратично (каждый save = перевставка ВСЕХ сообщений).

### 32. compress_session уничтожает ID и таймстемпы
- **core/memory_manager.py:186-196** — `delete_session()` + `create_session()` — теряются все оригинальные таймстемпы, auto-increment ID, FTS5 индексы.

### 33. F-string SQL-запросы в feedback
- **core/feedback.py:97-108** — SQL собирается через f-строки (хотя значения параметризованы, паттерн хрупкий).

### 34. EventBus не поддерживает async handlers
- **core/event_bus.py:16** — `handler(**kwargs)` без `await`. Если handler async, корутина создаётся, но никогда не выполняется → silent failure.

### 35. SQLite без threading lock в user_manager
- **core/user_manager.py:111,133,144,155,180,213,237** — `self._sqlite_conn` без блокировки. Конкурентные корутины → race condition.

### 36. Нет connection timeout в db_manager SQLite
- **core/db_manager.py:84-110** — `sqlite3.connect()` без timeout. Заблокируется навсегда при блокировке БД.

### 37. Silent `except: pass` в api_keys
- **core/api_keys.py:151-152** — Ошибки загрузки ключей (коррупция файла, I/O) проглатываются молча. Ключи не загрузятся без уведомления.

### 38. datetime.utcnow() deprecated (Python 3.12+)
- **core/feedback.py:56**, **core/scheduler_manager.py:222,229,253,259,314,320**, **web/a2a_server.py:89,123,203** — `datetime.utcnow()` → `DeprecationWarning`. Использовать `datetime.now(timezone.utc)`.

### 39. Демо-роутер не ловит все исключения
- **web/demo_router.py:168-170** — `except (RuntimeError, OSError)`. `KeyError`, `TypeError`, `ValueError`, `AttributeError` пролетают → unhandled 500.

### 40. subprocess.run() блокирует event loop
- **web/demo_router.py:202-211** — `subprocess.run()` (блокирующий) внутри async-endpoint'a. Блокирует весь event loop.

### 41. Неполная защита path traversal
- **web/demo_router.py:262-263** — `"/" in filename or ".." in filename` — не защищает от `....//`, null-byte (`\0`), encoded slashes (`%2F`).

### 42. ISO date сравнение без timezone
- **core/billing/plans.py:36** — Сравнение `month_start.isoformat()` (с timezone) с `created_at` (без timezone) → неправильные подсчёты.

### 43. Deprecated models.yaml конфликтует с configurator.py
- **config/models.yaml** — Помечен `DEPRECATED`, но всё ещё shipped. Другая структура профилей и имена: `deep_think` vs `smart`, `neuroapi` vs `fast`.

### 44. model_id с двойным prefix
- **skills/vision/skill.py:56,60** — `"openrouter/openai/gpt-4o-mini"` — double `openrouter/`. Стриппинг может сломаться при других значениях `VISION_MODEL`.

### 45. CLI TUI дублирует model profiles из configurator.py
- **cli/tui.py:92-96** — Хардкод имён моделей и версий, дублирующий `core/configurator.py`. При обновлении конфигуратора TUI отстанет.

### 46. JavaScript injection через строковую интерполяцию в browser skill
- **skills/browser/skill.py:175-183** — Экранирование только одинарных кавычек (`replace("'", "\\'")`), затем интерполяция в JS template literal. XSS через `</script>`, бэкслеши, etc.

### 47. SMTP без STARTTLS fallback
- **skills/email/skill.py:37** — Только `SMTP_SSL`. STARTTLS (порт 587) не поддерживается.

### 48. No-op `register_tools` в MCP Client
- **tools/mcp_client.py:58-63** — `register_tools()` и `unregister_tools()` — заглушки. MCPClient инициализируется, но не регистрирует инструменты. Мёртвый код.

### 49. Нет SSRF защиты в api_connector
- **tools/api_connector.py:5-38** — Любые URL принимаются: `http://169.254.169.254/latest/meta-data/` (cloud metadata), `http://localhost:6379` (Redis без auth).

### 50. Seed templates: `--idempotent` парсится, но не передаётся
- **scripts/seed_workflow_templates.py** — Аргумент `--idempotent` принимается argparse, но `seed()` вызывается без него. Флаг игнорируется.

### 51. Resolve_env_vars может получить строку вместо dict
- **core/orchestrator.py:49** — `resolve_env_vars(sub_config.get("model", {}))` — если model = `"kimi"` (строка), итерация по символам, не `.items()`.

### 52. Несоответствие портов: 8000 vs 8020
- Caddyfile → 8000, Docker → 8020, `agent.py serve` → 8000. Три конфликтующих конфига.

### 53. Orphaned COPY в Dockerfile
- **Dockerfile:5-6** — `COPY website/data ./website/data` в `/app/website/data`, но после смены WORKDIR этот путь больше не используется.

### 54. `resolve_env_vars` может получить строку вместо dict в orchestrator
- **core/orchestrator.py:49** — `resolve_env_vars(sub_config.get("model", {}))` — если `model` это строка (например `"kimi"`), `resolve_env_vars` будет итерироваться по символам строки вместо ключей dict.

---

## ⚪ LOW (15+)

- **llm_gateway.py:84-103** — `_try_fallback` определён, но никогда не вызывается (мёртвый код).
- **llm_gateway.py:7** — Unused import `async_jittered_backoff`.
- **db_manager.py:73** — Переменная `conninfo` вычисляется, но не используется.
- **scheduler_manager.py:219,226** — Дублирующийся `from core.db_manager import db` в одном методе.
- **db_migrate.py:34-35** — `import sqlalchemy` внутри `try/except` — маскирует `ModuleNotFoundError`.
- **web/server.py:87** — CORS origins не включают `localhost:8020` для Docker.
- **alembic.ini:5** — `sqlalchemy.url = sqlite:///data/agent.db` хардкод.
- **cli/tui.py:95** — Модель `smart` = `claude-sonnet-4`, без версии `-20250514`, в отличие от `configurator.py`.
- **requirements.txt:39,48** — `psycopg2-binary>=2.9.0` указан дважды.
- **pyproject.toml:21-66** vs **requirements.txt** — Версии зависимостей расходятся.
- **web/a2a_server.py:148** — Нет проверки, что вызывающий имеет право читать сообщения для `recipient`.
- **a2a_server.py:46-52** — `_memory_queue` (plain list) без cap/TTL/eviction → memory leak при падении Redis.
- **skills/slides/skill.py:275** — Хардкод `output/` директория.
- **tools/web_tools.py:38-39,49-51** — Несовместимые типы возврата: list на успех, dict с `error` на ошибку.
- **tools/vector_db.py:54,74** — Нет guard на `self._collection is None`.

---

## 📊 ИТОГО

| Severity | Count | Характеристика |
|----------|-------|---------------|
| 🔴 CRITICAL | 15 | **All RESOLVED** (2026-05-27 fix pass) |
| 🟠 HIGH | 12 | Гонки, потеря данных, race conditions, import error-ы, shell injection |
| 🟡 MEDIUM | 26+ | Утечки, дублирование, deprecated API, несовместимость конфигов |
| ⚪ LOW | 15+ | Мёртвый код, typo, хардкод, непоследовательности |

**Главные системные проблемы (статус 2026-05-27):**
1. **Три слоя БД** — **RESOLVED (partial)**: Alembic `005_unified_schema` — единый DDL; `create_tables()` deprecated; chat → `chat_sessions`/`chat_messages` в `agent.db`; PG через `PGStateManager` + Alembic
2. **Два session store** — **RESOLVED**: CLI и Web используют `get_state_db_path()` → `data/agent.db`; миграция: `scripts/migrate_state_to_agent.py`
3. **Два порта** — **RESOLVED**: канонический порт **8020** в Caddyfile, `agent.py`, `start_server.py`, CORS
4. **Две env var GitHub** — **RESOLVED**: `.env.example` → `GITHUB_TOKEN`; MCP configs → `GITHUB_PERSONAL_ACCESS_TOKEN`; `mcp_client_manager._resolve_env()`
5. **RCE** — **RESOLVED**: video `eval()` → `Fraction()`; data_analyst `run_python_code()` удалён (dead code)
6. **Runtime vs AgentRuntime** — **RESOLVED**: scheduler вызывает `await agent.run()` напрямую
7. **CRITICAL audit items #1–15** — **RESOLVED** (2026-05-27): MCP execute key, A2A queue pop, loop detection, cryptography dep, setup.bat, ORM autogenerate guard, browser page leak, slides export
8. **~30% функций/фич** — мёртвый код (см. остальной аудит) — **OPEN**
Теперь у меня полная картина. Вот подробный аудит.

***

# Аудит багов и gap-расхождений: `my-agent`

## TL;DR по критичности

Проект содержит около **20+ файлов документации** и **~4 параллельных точки входа**. Код технически сложный, но содержит ряд gap-расхождений между тем что задекларировано и тем что реально работает.

***

## 🔴 Критические баги (ломают запуск)

### BUG-01: React SPA не существует — `web/static/app/index.html` отсутствует в репо
`server.py` → `_serve_spa_index()` пытается открыть `web/static/app/index.html`. Этот файл **не находится в репозитории** — `web/static/app/` отсутствует как директория. Фолбэк идёт на `workflow-fallback.html`, и всё `/app/*` роутинг сваливается в него.  Фактически весь `/app`, `/app/chat`, `/app/onboarding` — битые.

### BUG-02: `store` используется в `/api/health` до инициализации
В `server.py` переменная `store = AgentStore()` объявлена ниже по файлу после всех `@app.on_event`, но `health()` обращается к `store.list_agents()` напрямую. При холодном старте если порядок импортов нарушен — `NameError`.

### BUG-03: Чат `/api/chat/stream` — `agent.memory.ensure_session()` это async, но не всегда
В `chat_stream()` вызывается `await agent.memory.ensure_session(sid)`. Если `MemoryManager` создан с `enabled=False`, метод может быть синхронным или вообще отсутствовать — падение с `AttributeError` без понятного сообщения.

### BUG-04: `AgentBuilder._get_cached_skill_loader()` — глобальный мутабельный кэш не thread-safe
`_skill_loader_cache` — модульная глобальная переменная. При конкурентных async запросах возможна race condition: несколько coroutine одновременно увидят `_skill_loader_cache is None` и начнут создавать `SkillLoader`, потенциально перезаписывая друг друга.

### BUG-05: `AuthMiddleware` — `ACTIVE_SESSIONS.dec()` в `finally` при редиректах не работает
`ACTIVE_SESSIONS.inc()` вызывается до `try`, но `ACTIVE_SESSIONS.dec()` — в `finally` **внутри `try`**. При `return RedirectResponse(...)` (onboarding редирект) код достигает `finally` корректно, но только если не поднято исключение в `resolve_workspace`. При исключении — dec не вызывается. Prometheus gauge будет бесконечно расти.

***

## 🟠 Серьёзные gap-расхождения

### GAP-01: `demo_router.py` — реальный режим (`real=True`) никогда не активируется по умолчанию
Демо-роутер по умолчанию запускает mock. Флаг `real=True` требует наличия ключа в env, но нет кода который бы **автоматически проверил** наличие ключа и переключился. Пользователь может вечно смотреть скрипт не подозревая об этом.

### GAP-02: `scripts/seed_workflow_templates.py` не вызывается в `startup()`
`startup()` в `server.py` не содержит вызова сидинга шаблонов. `demo_router` при 503 говорит «запустите seed-скрипт», но это ручная операция. Свежий `docker-compose up` = нет шаблонов = демо падает с 503.

### GAP-03: Три параллельных entrypoint — непонятно что запускать
Корень репо: `agent.py` (11 KB), `agent_backup.py` (35 KB!), `agent_styled.py` (20 KB), `start_server.py` (1.4 KB). Ни один файл не обозначен как "deprecated". Новый разработчик не знает что запустить.

### GAP-04: `/chat` и `/agents` — legacy HTML файлы vs React SPA
`server.py` имеет legacy-роуты `GET /chat` → `web/static/chat.html`, `GET /agents` → `web/static/agents.html`, **одновременно** с `AuthMiddleware` который редиректит `/chat` → `/app/chat`. Возникает бесконечный редирект для авторизованного пользователя: `/chat` → `301 /app/chat` → `/app/chat` → `_serve_spa_index()` → фолбэк.

### GAP-05: `requirements.txt` vs `pyproject.toml` — дублирование и конфликты
Репо содержит и `requirements.txt`, и `pyproject.toml`. Они не синхронизированы — `pyproject.toml` содержит расширенный список с версиями, `requirements.txt` — облегчённый без версий. Непонятно что использовать в Dockerfile.

### GAP-06: WebSocket `/ws/chat` — агент запускается как `await agent.run(message)` без стриминга
Вместо нативного стриминга токенов WebSocket-обработчик вызывает `await agent.run(message)` (блокирует), ждёт полный ответ, **потом** режет его на куски по 100 символов и шлёт как `{type: chunk}`. Это имитация стриминга, не реальный стриминг. Задержка перед первым чанком = полное время LLM inference.

### GAP-07: `LLMGateway.chat_stream()` yield после ошибки не сбрасывает `tool_calls_buffer`
При ошибке внутри цикла async-for по чанкам `tool_calls_buffer` может содержать незавершённые tool_calls. После fallback они будут yield-нуты повторно или потеряны. Это приводит к дублированию или потере tool_call событий в UI.

***

## 🟡 Средние баги и code smell

### BUG-06: `server.py` — `_set_auth_cookie` дублирует `set_auth_cookie`
На строке ~290: `def _set_auth_cookie(response, token): set_auth_cookie(response, token)` — мёртвая обёртка, нигде не используется.

### BUG-07: `builder.py` — `enable_compression()` устанавливает `self._max_tokens`, но `build()` читает `getattr(self, "_max_tokens", 4000)` через getattr-fallback
Если `enable_compression()` **не вызвать явно**, то `self._enable_compression = True` (по умолчанию), но `self._max_tokens` не существует — `getattr` вернёт `4000`. Это маскирует отсутствие явной конфигурации, не поднимает исключение.

### BUG-08: `chat_stream` — `workspace_id` переопределяется в середине функции
Внутри `event_stream()` на строке ~450: `workspace_id = getattr(request.state, "workspace_id", None)` — переменная `workspace_id` уже существует во внешнем scope `chat_stream`. Это closure-shadowing: внутри генератора создаётся локальная переменная с тем же именем, которая перекрывает внешнюю. В Python это не ошибка, но потенциальный источник путаницы при рефакторинге.

### GAP-08: `CORS` разрешает только localhost — продакшн заблокирован
`allow_origins` содержит только `localhost:3000/5173/8000` и `127.0.0.1:8000`. При деплое на VPS фронтенд по домену будет получать CORS 403 на все API запросы. Нет переменной окружения для конфигурации allowed origins.

### GAP-09: `AuthMiddleware` не применяется к WebSocket-роутам
`/ws/chat` и `/ws/room/{room_id}` имеют **собственную** auth через `_authenticate_websocket`. Но `AuthMiddleware` (который проверяет `is_public_path`) не знает о WebSocket-путях. Если `is_public_path("/ws/chat")` вернёт `False`, Middleware попытается обработать WS-хендшейк как обычный HTTP-запрос — без cookie это приведёт к редиректу на `/login` **до** того как WS-обработчик успеет аутентифицировать соединение.

### GAP-10: `AlembicMigrations` присутствует рядом с `db_manager.py` ручными `CREATE TABLE`
`startup()` вызывает и `run_migrations()` (Alembic), и `db.create_tables()` (ручные SQL), и отдельные `db.execute("CREATE TABLE IF NOT EXISTS scheduled_jobs_log")`. Три системы управляют схемой одновременно. Конфликт почти неизбежен при добавлении новых полей.

***

## 📊 Инвентаризация gap по слоям

| Слой | Заявлено | Реальность |
|---|---|---|
| **SPA фронтенд** | React app на `/app/*` | Файл `web/static/app/index.html` отсутствует → фолбэк |
| **Чат стриминг** | Real-time SSE токены | SSE работает через `llm.chat_stream()`, но WS делает псевдо-стриминг |
| **Демо** | Живой агент | Mock по умолчанию, seed не автоматизирован |
| **Auth** | JWT + Redis токены | Работает, но WS-роуты могут быть заблокированы Middleware |
| **Schema management** | Alembic | 3 системы параллельно — Alembic + create_tables + raw SQL |
| **Entrypoints** | Один `agent.py` | 4 файла: agent.py, agent_backup.py, agent_styled.py, start_server.py |
| **CORS** | Продакшн-ready | Только localhost |
| **Skill loader** | Кэш для performance | Глобальный мутабельный без lock — race condition при конкурентных запросах |

***

## Приоритет исправлений для живого демо

1. **BUG-01** — разобраться где SPA: либо собрать React, либо убрать dead fallback и сделать нормальный UI
2. **GAP-02** — добавить `seed_workflow_templates` в `startup()`
3. **GAP-01** — сделать явный индикатор mock vs real в UI
4. **GAP-03** — удалить `agent_backup.py` и `agent_styled.py` из корня
5. **GAP-06** — починить WS: использовать `llm.chat_stream()` вместо `agent.run()` + нарезки
