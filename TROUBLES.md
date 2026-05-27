# АУДИТ БАГОВ И РАСХОЖДЕНИЙ: my-agent

> Дата: 2026-05-27 (re-audit post-remediation — после sprint TROUBLES fix)
> Предыдущий: аудит #11 — независимый code audit, CLI-сессия

---

## Re-audit post-remediation — 2026-05-27

Повторная проверка после sprint TROUBLES fix (2026-05-27).
Метод: автоматический gate + grep spot-checks + security one-liners + TestClient smoke.

### Gate

| Проверка | Результат |
|----------|-----------|
| `git ls-files .env` | **PASS** — не tracked |
| `uv build` | **PASS** |
| `bash scripts/check-secrets.sh` | **PASS** |
| pytest gate (60 tests) | **PASS** — 60/60 |
| `import web.server` (136 routes) | **PASS** |
| `alembic upgrade head` (SQLite dev) | **PASS** |
| `grep _resolve_db_url alembic/env.py` | **PASS** |

### Spot-checks

| Проверка | Результат |
|----------|-----------|
| Phase 1: setuptools / JS file-exec / file_tools / CI secrets | **PASS** |
| Security: path traversal blocked | **PASS** |
| Security: JS no shell injection | **PASS** |
| Phase 2: user_manager to_thread, feedback lazy db, lazy startup | **PASS** |
| Phase 2: CORS_ORIGINS, get_client_ip | **PASS** |
| Phase 2: memory replace_messages, alembic DATABASE_URL | **PASS** |
| fail-closed admin (`ENV=production`, empty DB) | **PASS** |
| TestClient smoke (health, metrics, stats) | **PASS** |
| Content-Length guard (`GET /api/health`, bad header) | **PASS** — 400 |
| Phase 3: Prometheus middleware metrics present | **PASS** |
| Phase 3: tests/conftest.py auth_client | **PASS** |
| Phase 4: MCP path, demo_router, session_cache, agent_store, compose, MCP lock | **PASS** |
| CORS_ORIGINS merge (unit) | **PASS** |
| get_client_ip X-Forwarded-For (unit) | **PASS** |

**Заметки:**

- fail-closed admin на **существующей** БД с user `admin` не бросает ошибку (ожидаемо — возвращает существующего admin). Тест валиден только на пустой `users` table.
- Content-Length на `POST /api/chat` без auth даёт 401 до middleware; проверять на public route (`/api/health`).
- Alembic PG на prod не прогонялся локально (нет PG в gate); `_resolve_db_url()` в коде — **PASS**.

### Remediation: что закрыто (аудит #11 + часть #10)

| ID | Было | Статус |
|----|------|--------|
| #11 C1 | pyproject flat-layout | **FIXED** |
| #11 H1 | sync sqlite в user_manager | **FIXED** — `asyncio.to_thread` |
| #11 H2 | feedback eager db | **FIXED** — lazy `_get_db()` |
| #11 H3 | CORS `*` | **FIXED** (был stale) — localhost + `CORS_ORIGINS` |
| #11 H4 | rate limit без XFF | **FIXED** — `get_client_ip()` |
| #11 M1 | load_all_keys at import | **FIXED** — `_init_agent_runtime()` |
| #11 M2 | test_memory_manager FTS | **FIXED** — LIKE fallback |
| #11 M3 | Prometheus middleware | **FIXED** |
| #10 C2 | JS command injection | **FIXED** — `run_javascript()` file mount |
| #10 C3 | file_tools path traversal | **FIXED** — `AGENT_WORKSPACE` sandbox |
| #10 H1/H2 | memory save_session dup / compress | **FIXED** — `replace_messages` |
| #10 H8 | alembic hardcode SQLite | **FIXED** — `DATABASE_URL` in env.py |
| #10 H4/H5 | default admin password | **FIXED** — fail-closed prod + wizard reject |

### OPEN после remediation (backlog, не регрессия)

| ID | Тема | Статус |
|----|------|--------|
| H13 | Wizard пишет ключи в `.env` plaintext | OPEN |
| H9 | Docker sandbox в контейнере (docker.sock) | OPEN — документировать в README/deploy |
| M8 | `asyncio_mode=auto` vs `asyncio.run()` в тестах | PARTIAL — conftest есть, миграция неполная |
| M2-chunked | Chunked encoding bypass | OPEN |
| M11 | permissions.py FastAPI coupling | OPEN |
| M6-pg | pg_state destructive DROP TABLE | OPEN |
| Skills | transcribe_audio dup, web_scrape dup, docs `<ul>` | OPEN |
| Infra | Caddy в compose, n8n depends_on | OPEN |
| #11 L1 | `_user_session_id()` `::` collision | OPEN |
| L* | dead imports, registry.json missing tools | LOW backlog |

### Verdict

**Критерий успеха re-audit: ВЫПОЛНЕН.**

Recommendation: **READY for commit** (gate green). OPEN items — отдельные PR в Phase 3+ backlog.

### Re-audit checklist (выполнен)

```bash
cd ~/dev/my-agent && source .venv/bin/activate
git ls-files .env
uv build && bash scripts/check-secrets.sh
pytest tests/test_code_tools.py tests/test_file_tools.py \
       tests/test_security_improvements.py tests/test_async_utils.py \
       tests/test_db_manager.py tests/test_production_hardening.py \
       tests/test_all.py::test_memory_manager -q
python -c "from web.server import app; print(len(app.routes), 'routes')"
alembic upgrade head
```

---

## 🔴 Аудит #11 — НОВЫЕ НАХОДКИ (2026-05-27)

> **Статус после re-audit post-remediation:** пункты C1, H1–H4, M1–M3 из секции ниже — **FIXED**. Остаётся open: L1.

Выполнен независимый аудит в CLI-сессии: импортированы все 74 Python-модуля (core/ 42, web/ 11, tools/ 21),
запущен веб-сервер (FastAPI стартует, 136 routes), выполнены тесты.

**Аудит #11 обнаружил 8 проблем, не учтённых в аудите #10:**

### Критическая цепочка: Build → Runtime → Deadlock

```
pyproject.toml (flat-layout) ──> pip install -e . падает ──> проект нельзя установить
        │
        └──> pyproject.toml asyncio_mode=auto ──> RuntimeError: already running loop в 30+ тестах
```

```
user_manager.py (sync sqlite3 в async) ──> блокировка event loop на каждом DB-запросе
        │
        ├──> create_default_admin() ──> INSERT без run_in_executor ──> сервер не отвечает
        └──> get_user_by_id() ──> SELECT без run_in_executor ──> race condition при конкурентных запросах
```

```
feedback.py (singleton db при импорте) ──> если DATABASE_URL невалиден ──> весь модуль падает
        │
        └──> submit_feedback() дёргается из WebSocket/API ──> 500 ошибка, потеря отзыва
```

---

### 🔴 CRITICAL (1) — Исправить немедленно

| # | Файл | Строки | Баг | Цепочка: причина → следствие |
|---|------|--------|-----|------------------------------|
| C1 | `pyproject.toml` | — | **Build broken (flat-layout)**: отсутствует `[tool.setuptools.packages.find]`. `pip install -e .` падает с `error: Multiple top-level packages discovered in a flat-layout`. `uv build` тоже падает. Причина: setuptools ≥64 требует явного указания include/exclude когда в корне >1 пакета (core, web, tools, cli, tests) | Нельзя установить пакет → `pip install -e ".[dev]"` не работает → зависимости не резолвятся → uv run --with тоже падает → разработка и тестирование возможны только из `PYTHONPATH=.` |

---

### 🟠 HIGH (4) — Сломают продакшн или блокируют event loop

| # | Файл | Строки | Баг | Цепочка: причина → следствие |
|---|------|--------|-----|------------------------------|
| H1 | `core/user_manager.py` | 77 | **sync sqlite3 в async методе**: `async def _init_sqlite(self, conn_params)` (и все остальные методы: `create_user`, `get_user_by_id`, `verify_user`) используют `sqlite3.connect()` и `cursor.execute()` напрямую, **без `asyncio.to_thread`** или `run_in_executor`. Вся работа с SQLite синхронная внутри async-функций | FastAPI вызывает async endpoint → `user_manager.get_user_by_id()` → `_cursor.execute()` блокирует thread на IO → event loop не может обработать другие запросы → под нагрузкой latency растёт, сервер перестаёт отвечать |
| H2 | `core/feedback.py` | 11 | **Singleton `db` на уровне модуля**: `from core.db_manager import db` — `db = DBManager()` создаётся при первом импорте модуля. Если `DATABASE_URL` пустой или невалидный, или БД недоступна — `DBManager.__init__()` падает. Нет lazy-init, нет graceful degradation | Любой код делает `from core.feedback import submit_feedback` → триггерит `from core.db_manager import db` → если DBManager крешится → **весь модуль feedback не импортируется** → любой API-эндпоинт, использующий feedback, падает с ImportError |
| H3 | `web/server.py` | 22, 60-63 | **CORS `allow_origins=["*"]`**: CORS middleware настроен на приём запросов с любого origin. Нет проверки `Origin` header, нет `allow_origin_regex`. В комбинации с `allow_credentials=True` — **нарушение спецификации CORS**: `Access-Control-Allow-Origin: *` + `Access-Control-Allow-Credentials: true` не должен работать вместе (браузеры игнорируют credentials при `*`). Но главное — любой сайт может делать `fetch()` к API и читать ответ | Злоумышленник создаёт сайт → пользователь авторизован в my-agent → скрипт делает fetch к /api/keys → браузер (в норме) блокирует, но из-за `*` разрешает → **API-ключи и данные утекают на сторонний сайт** |
| H4 | `web/server.py` | 315-326, 740-755 | **Rate limiting использует client IP без X-Forwarded-For**: `limiter.limit(...)` (slowapi) по умолчанию берёт `request.client.host`. При reverse proxy (nginx/Caddy) все запросы приходят с IP прокси — rate limit бьёт по одному IP для всех пользователей. Нет парсинга `X-Forwarded-For`/`X-Real-IP` | Запросы через Caddy/nginx → rate limit считается на IP 127.0.0.1 или 172.x.x.x → **1 пользователь-спамер блокирует rate limit для всех** ИЛИ наоборот: **rate limit на конкретного пользователя не срабатывает, т.к. IP общий** |

---

### 🟡 MEDIUM (3) — Некорректное поведение, утечки

| # | Файл | Строки | Баг | Цепочка: причина → следствие |
|---|------|--------|-----|------------------------------|
| M1 | `web/server.py` | 344-345 | **`load_all_keys_to_env()` — модульный side effect**: вызывается на уровне модуля при импорте `web.server`. Читает зашифрованные ключи из БД и проставляет в `os.environ`. Если БД недоступна или ключи повреждены — падает при импорте, до старта приложения | `import web.server` → `load_all_keys_to_env()` → DB error → **весь сервер не стартует**. Невозможно тестировать отдельные модули без полной инициализации БД |
| M2 | `tests/test_all.py` | 94-146 | **test_memory_manager FAIL**: `assert len(results) > 0` при `mm.search("Hello")` возвращает пустой список `[]`. Сообщения сохраняются в БД (get_session возвращает 3 сообщения), но FTS5 поиск не находит их. Возможно: FTS5-индекс пуст (триггер `chat_messages_fts_insert` не сработал) или токенизация FTS5 не совпадает | Тест `test_memory_manager` FAIL → не тестируется поиск → **search_messages может падать в продакшне** без предупреждения. Агенты не смогут искать в истории диалогов |
| M3 | `web/server.py` | 329-335 | **Prometheus `/metrics` без middleware**: endpoint существует и возвращает метрики из `_prom_registry`, но **`PrometheusMiddleware` не подключён**. Нет авто-сбора `requests_total`, `request_duration_seconds`, `requests_in_progress`. Единственная метрика — `ACTIVE_SESSIONS` (SSE/WS gauge) | Нет latency/error rate метрик → мониторинг не видит degradation → **prod-инциденты пропускаются**. Grafana панели пустые |

---

### 🔵 LOW (1) — Слабое место

| # | Файл | Строки | Баг | Цепочка |
|---|------|--------|-----|---------|
| L1 | `web/server.py` | 734-737 | **`_user_session_id()` коллизия**: сессионный ключ строится как `f"{user_id}::{raw_sid}"`. Если `raw_sid` от клиента содержит `::` (например, base64-encoded данные), ключи разных пользователей/сессий могут пересечься | Редкий edge-case → пересечение session_id → сообщения одного пользователя видны другому → **утечка истории диалогов** |

---

### 📊 Обновление динамики (аудит #11)

| Итерация | CRITICAL | HIGH | MEDIUM | LOW |
|----------|----------|------|--------|-----|
| Аудит #11 (свежие) | +1 | +4 | +3 | +1 |
| Аудит #10 | +3 | +17 | +22 | +23 |
| Итого open с учётом #11 | **4** | **21** | **25** | **24** |

---

## 🔴 Аудит #10 — НОВЫЕ НАХОДКИ (2026-05-27)

Выполнен независимый аудит 80+ Python-файлов. Предыдущие аудиты #6–#9 закрыли 13 CRITICAL и 16 HIGH.
**Аудит #10 обнаружил 65+ новых проблем**, не учтённых в предыдущих спринтах:

### Критическая цепочка: Security → Data Loss → Runtime Crash

```
.env (живые ключи) ──> command injection (_run_javascript) ──> path traversal (file_tools)
       │
       ├──> Docker COPY . . ──> ключи утекают в образ
       └──> .dockerignore не защищает node_modules ──> 500MB мусора в build context
```

```
memory_manager.save_session ──> дубликаты сообщений при каждом вызове
       │
       └──> compress_session неатомарна ──> креш между delete/create = потеря сессии
```

```
alembic.ini → sqlite:///data/agent.db (hardcode)
       │
       └──> env.py не читает DATABASE_URL ──> в продакшне миграции бьют в SQLite, а не PostgreSQL
```

---

### 🔴 CRITICAL (3) — Исправить немедленно

| # | Файл | Строки | Баг | Цепочка: причина → следствие |
|---|------|--------|-----|------------------------------|
| C1 | `.env` | 8,10 | **Живые API-ключи в открытом виде**: `OPENROUTER_API_KEY=sk-or-v1-...`, `TAVILY_API_KEY=tvly-dev-...`. Закоммичены в git-репозиторий. Dockerfile: `COPY . .` — ключи попадают в образ | `.env` не зашифрован → `COPY . .` в Dockerfile → любой, имеющий доступ к образу, получает ключи → компрометация OpenRouter и Tavily аккаунтов |
| C2 | `tools/code_tools.py` | 61-62 | **Command Injection**: `escaped = code.replace("'", "'\"'\"'")` — экранирование single-quote. Пайлоад типа `'); rm -rf /; '` или `$(cat /etc/passwd)` пробивает shell-контекст | LLM генерирует вредоносный JS → `_run_javascript` вставляет его в `bash -c '...'` → shell-инъекция → RCE на хосте Docker или в контейнере |
| C3 | `tools/file_tools.py` | 7, 15 | **Path Traversal**: `path` от LLM передаётся напрямую в `open(path)`. Никакого sandbox-а или проверки `..` | LLM запрашивает `file_read('../../.env')` → агент читает любые файлы системы → утечка всех секретов, кода, данных |

---

### 🟠 HIGH (17) — Сломают продакшн или теряют данные

| # | Файл | Строки | Баг | Цепочка: причина → следствие |
|---|------|--------|-----|------------------------------|
| H1 | `core/memory_manager.py` | 97-111 | **save_session дублирует сообщения**: `for msg in session.messages` — вызывает `add_message` без проверки на уникальность. Каждый вызов пересохраняет всю историю | Каждый запрос в чате вызывает `save_session` → размер БД растёт линейно с каждым диалогом → history越长, резко падает производительность, растёт стоимость LLM (контекст раздувается дубликатами) |
| H2 | `core/memory_manager.py` | 162-197 | **compress_session неатомарна**: `delete_session` + `create_session` + insert — между delete и create может упасть процесс | Сервер падает между delete и create → **все сообщения сессии потеряны безвозвратно** |
| H3 | `core/mcp_client_manager.py` | 90-113 | **Race condition на stdio**: `_send_stdio` и `_recv_stdio` вызываются через `asyncio.to_thread` без `threading.Lock`. Конкурентные async-таски могут перемешивать запись в stdin subprocess | Два агента одновременно пишут в MCP stdio → JSON-RPC линии склеиваются → `json.loads` падает → MCP-соединение разрывается |
| H4 | `core/wizard.py` | 180-182 | **Weak password по умолчанию**: если введён пароль < 12 символов, тихо проставляется `admin_password = "admin"` | Пользователь вводит короткий пароль → система молча ставит `"admin"` → веб-интерфейс доступен любому знающему стандартный пароль |
| H5 | `core/user_manager.py` | 160-165 | **Дефолтный admin пароль "admin"**: `os.environ.get("AGENT_PASSWORD", "admin")` — если переменная не задана, создаётся admin/admin | Первый запуск → admin не создан → `create_default_admin` → пароль "admin" → полный доступ к системе |
| H6 | `core/auto_agent_factory.py` | 42-43 | **Wrong agent ID**: если `save_agent()` первого sub-agent упал, но `len(sub_configs) == 1`, то `orchestrator.run(task, temp_ids[0])` получает ID несуществующего агента | Sub-agent создался в памяти → save упал → orchestrator пытается запустить по ghost-ID → **RuntimeError: agent not found** |
| H7 | `tests/test_real_api.py` | 155,190,212,230,252,276 | **Отсутствует фикстура `auth_client`**: используется в 3 test-классах, но не определена в файле. Нет `conftest.py` | `pytest tests/test_real_api.py` → `fixture 'auth_client' not found` → 3 класса тестов (12+ тестов) не запускаются → **UX/интеграционные тесты молча пропущены** |
| H8 | `alembic.ini` + `alembic/env.py` | 5 + 44-48 | **Миграции всегда в SQLite**: `sqlalchemy.url = sqlite:///data/agent.db` hardcoded. `env.py` читает из `alembic.ini`, игнорируя `DATABASE_URL` | В продакшне (Docker) БД = PostgreSQL → `alembic upgrade head` бьёт в `/app/data/agent.db` (SQLite) → **схема PostgreSQL никогда не обновляется**, таблицы не создаются |
| H9 | `Dockerfile` + `docker-compose.yml` | — | **Docker sandbox не работает в контейнере**: нет `/var/run/docker.sock`, не установлен `docker.io` CLI | `code_tools.execute_code` вызывает `docker_sandbox` → Docker недоступен → **весь запуск кода (python/js/bash) возвращает ошибку** |
| H10 | `.dockerignore` | 9-10 | **node_modules не исключается**: паттерны `frontend/node_modules` и `frontend/dist` — относительные. Реальные пути: `web/frontend/node_modules` | `docker build` → Docker daemon получает ~500MB node_modules → сборка длится минуты, образ раздут |
| H11 | `requirements.txt` | — | **Отсутствуют 5+ зависимостей** из `pyproject.toml`: `docker>=7.0`, `pillow>=10.0`, `python-telegram-bot>=21.0`, `discord.py>=2.3`, `slack-sdk>=3.27` | `pip install -r requirements.txt` → импорт этих пакетов в рантайме → **ModuleNotFoundError** |
| H12 | `run_api_test.py` | 28,35,38,41,56 | **`os.environ[key]` без try/except**: `os.environ['NEUROAPI_API_KEY']` — если не задан → KeyError | Тестовый скрипт сразу падает с traceback, не давая понять что не так |
| H13 | `core/wizard.py` + `core/auth.py` | 116-201 / 39-58 | **Plaintext хранилище кредов**: API-ключи и пароль пишутся в `.env` (wizard) и `wizard_config.json` в незашифрованном виде | Компрометация файловой системы → все API-ключи и пароль утекают |
| H14 | `web/server.py` | 483-488 | **Module-level side effects**: `AgentStore()`, `Orchestrator()`, `AutoAgentFactory()` — инициализация на уровне импорта | `import web.server` → читает `agents/registry.json`, создаёт Orchestrator, LLMGateway → ошибка при импорте убивает весь процесс. Тесты не могут замокать эти объекты |
| H15 | `web/server.py` | 876-878 | **Unsanitized JSON в config**: admin endpoint пишет user-supplied JSON в `config/agent.json` без валидации | Админ отправляет кривой JSON → файл конфига повреждён → сервер не стартует при следующем запуске |
| H16 | `core/scheduler_manager.py` | 298 | **Hard import Gmail**: `from skills.gmail.skill import gmail_list_unread` — на уровне тела функции, но безусловно | Если `skills/gmail/skill.py` содержит import error → весь `scheduler_manager` падает → **запланированные задачи не исполняются** |
| H17 | `core/config.py` | 52-59 | **`_merge` мутирует `DEFAULT_CONFIG`**: `result = default.copy()` — shallow copy. Вложенные dict-ы разделяются между вызовами | Два разных `load_config()` с разными override → первый вызов может изменить `DEFAULT_CONFIG` через мутацию вложенного dict → второй вызов получает некорректные данные |

---

### 🟡 MEDIUM (22) — Некорректное поведение, логические ошибки

| # | Файл | Строки | Баг | Цепочка |
|---|------|--------|-----|---------|
| M1 | `web/server.py` | 104 | **`int(content_length)` ValueError**: заголовок `Content-Length: abc` → 500-ошибка | Злоумышленник шлёт кривой header → request size limit bypass через exception |
| M2 | `web/server.py` | 106 | **Chunked encoding bypass**: лимитер проверяет только `Content-Length`, не читает `Transfer-Encoding: chunked` | Злоумышленник шлёт 1GB chunked body → размер не проверяется → OOM |
| M3 | `web/mcp_server.py` | 148-153 | **Path traversal через MCP URI**: `skill://../../../etc/passwd` → `skills/{name}/README.md` → `skills/../../../etc/passwd/README.md` — на Linux переход в `/etc` не сработает, но `skill://../../README.md` прочитает README.md проекта | Аутентифицированный пользователь запрашивает `skill://../../config/agent.json` → читает конфиг с API-ключами |
| M4 | `web/demo_router.py` | 27 | **CWD-зависимые пути**: `Path("data/demo")` — при запуске не из корня проекта всё ломается | `cd /opt && python /app/web/server.py` → demo-эндпоинты возвращают 404, т.к. `data/demo` не найден |
| M5 | `web/a2a_server.py` | 126-143 | **`_memory_queue` игнорируется при живом Redis**: сообщения в памяти накапливаются, пока Redis не упадёт. Доставляются только при следующем фейле Redis | Redis пал → все накопленные сообщения вываливаются разом → out-of-order delivery |
| M6 | `core/pg_state.py` | 67-76 | **Деструктивный DROP TABLE ... CASCADE**: при обнаружении legacy колонки — безвозвратно удаляет таблицу `sessions` | Первый запуск с PostgreSQL → `_migrate_from_legacy_if_needed` → DROP TABLE sessions CASCADE → **потеря всех legacy-данных** |
| M7 | `core/eval/prompt_eval.py` | 53 | **Self-bias оценка**: один `LLMGateway` и генерирует ответ, и оценивает его | Модель склонна оценивать свой же ответ выше → метрики качества завышены |
| M8 | `tests/` (множество) | — | **`asyncio.run()` + `asyncio_mode=auto`**: тесты используют `asyncio.run()` внутри синхронных функций. `pyproject.toml` включает `asyncio_mode = "auto"` | `pytest` собирает тесты → async def-функции прогоняются в существующем event loop → `asyncio.run()` изнутри → **RuntimeError: cannot run from running event loop** |
| M9 | `core/validation.py` | 29, 32 | **`output_dir` хардкод `os.path.abspath("output")`** + **`".." in path` false positive** | Смена CWD → validation ложно отклоняет/принимает пути |
| M10 | `core/pg_state.py` | 115 | **Пустой `[]` tool_calls → NULL**: `json.dumps(kwargs.get("tool_calls")) if kwargs.get("tool_calls") else None` — пустой список falsy | Сообщение с `tool_calls=[]` сохраняется как `tool_calls=NULL` → при загрузке теряется информация |
| M11 | `core/teams/permissions.py` | 5, 25 | **FastAPI coupling**: `raise fastapi.HTTPException` из core-модуля | Вызов `check_permission` из CLI/фонового скрипта → импорт FastAPI → crash если нет FastAPI |
| M12 | `core/agent_store.py` | 34 | **`agent["id"]` KeyError**: если `registry.json` содержит entry без `"id"` | Повреждённый registry → `get_agent` падает с KeyError |
| M13 | `core/state_db.py` | 540-553 | **duplicate messages**: `create_session` (INSERT OR IGNORE) + `delete_messages` + re-insert — если delete упал, остаются дубликаты | Сбой БД в середине → часть старых сообщений + часть новых → дубликаты |
| M14 | `core/builder.py` | 22-23 | **Race condition на `_skill_loader_cache`**: два прохода check-then-set | Два синхронных запроса → оба видят `None` → создают два загрузчика |
| M15 | `web/server.py` | 412-414 | **`_set_auth_cookie()` — dead code**: определена на строке 412, нигде не вызвана (наст. версия на стр. 407 вызывает `set_auth_cookie` напрямую) | Мёртвая обёртка, вводит в заблуждение при чтении кода |
| M16 | `requirements.txt` | 39,48 | **Дубликат**: `psycopg2-binary>=2.9.0` дважды | `pip install` — второй раз просто переустановит тот же пакет, но это баг поддержки |
| M17 | `requirements.txt:47` vs `pyproject.toml:58` | — | **Version drift**: `httpx>=0.27.0` vs `>=0.28.0` | После `pip install -r requirements.txt` версия httpx может не совпадать с ожидаемой в pyproject |
| M18 | `web/demo_router.py` | 207-209 | **`subprocess.run(..., check=False, no timeout)`**: молча swallows ошибку + может повесить event loop | Дочерний процесс завис → subprocess.run ждёт вечно → event loop заблокирован → **весь сервер не отвечает** |
| M19 | `Caddyfile` | 7 | **Caddy не в compose**: `reverse_proxy my-agent:8020` — но Caddy сервиса нет в `docker-compose.yml` | `docker compose up` → Caddy нет → reverse_proxy не работает |
| M20 | `docker-compose.yml` | 9 | **`version: "3.8"` deprecated**: Docker Compose v2 игнорирует поле с warning | `docker compose up` → warning message на каждую команду |
| M21 | `tests/test_production.py` | 33 | **Тавтология**: `assert d1 != d2 or True` — всегда True | Тест на jitter никогда не упадёт, даже если jitter сломан |
| M22 | `tests/test_db_manager.py` | 92-98 | **Пустой тест**: `test_fallback_to_sqlite` — тройной `with patch(...)` вокруг `pass` | Бесполезный тест, создаёт false sense of coverage |

---

### 🔵 LOW (23) — Косметика, dead code, дубликаты, стайл

| # | Файл | Строки | Баг |
|---|------|--------|-----|
| L1 | `agent.py` | 53,60 | **Redundant re-import**: `resolve_env_vars` уже импортирован на строке 15 |
| L2 | `core/orchestrator.py` | 3 | **Unused import**: `run_parallel_agents` из `core.sub_agents` |
| L3 | `core/runtime.py` | 134 | **`import asyncio` внутри тела метода** |
| L4 | `core/db_manager.py` | 73-74 | **Dead code**: `conninfo = self.database_url.replace(...)` — вычисляется, не используется |
| L5 | `core/logger.py` | 24 | **`os.makedirs("")` crash**: если `log_file` без directory component |
| L6 | `core/session_cache.py` | 202 | **Double prefix**: `key = f"ratelimit:{action}:{identifier}"` + redis_client снова добавляет `ratelimit:` → ключи `ratelimit:ratelimit:...` |
| L7 | `core/eval/quality_metrics.py` | 50 | **Potential ZeroDivision**: `max_ref_len` может быть 0 при пустом `references`, но guard есть — LOW |
| L8 | `core/workflow/executor.py` | 35-37 | **O(n²) запись логов**: `update_run_logs` перезаписывает весь массив логов при каждом новом эвенте |
| L9 | `core/workflow/validator.py` | 59-79 | **Дубликат `_has_cycle`**: идентичная функция есть в `executor.py:456-462` |
| L10 | `core/workflow/nodes/agent.py` | 15 | **Module-level AgentStore()**: креш при импорте, если `registry.json` битый |
| L11 | `core/feedback.py` | 142 | **Shadow builtin**: `def export_training_dataset(format: str = "jsonl")` — `format` переопределяет встроенную функцию |
| L12 | `tools/data_tools.py` | 3 | **Unused import**: `subprocess` |
| L13 | `web/server.py` | 7, 22 | **Unused imports**: `traceback`, `DEFAULT_CONFIG` |
| L14 | `web/mcp_server.py` | 67, 79 | **Private attr access**: `registry._tools` вместо публичного API `list_all()/get()` |
| L15 | `web/a2a_server.py` | 165,219,248,269 | **Unused params**: `request: Request` — приняты, не используются |
| L16 | `web/auth_router.py` | 95 | **Deferred circular import**: `from web.server import user_manager` внутри функции |
| L17 | `cli/tui.py` | 33 | **Unused import**: `SKILLS_DIRS` |
| L18 | `core/skill_cache.py` | 33 | **Dead mapping**: `read_source` → нет реализации нигде в коде |
| L19 | `agents/registry.json` | — | **Нет регистрации тулов**: `list_tables`, `ocr_pdf`, `browser_*`, `schedule_task`, `github_list_issues` и др. — заявлены, но не зарегистрированы |
| L20 | `scripts/entrypoint.sh` | 5 | **Флаг `--idempotent` игнорируется**: передан в `seed_workflow_templates.py`, который не парсит sys.argv |
| L21 | `.env.example` vs `.env` | — | **Дрейф переменных**: `KIMI_API_KEY` выключен в `.env`, активен в `.env.example`; `GOOGLE_AUTH_*` в `.env.example` — нет в `.env` |
| L22 | `tools/code_tools.py` | 40,59,81 | **`timeout` игнорируется**: все 3 runner принимают `timeout`, но не передают в `docker_sandbox` (используется `self.timeout=30`) |
| L23 | `docker-compose.yml` | 42-59 | **Нет `depends_on` для n8n**: агент может обратиться к n8n до его готовности |

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
| **Аудит #10** | **+3** | **+17** | **+22** | **+23** |

---

## ⏳ ОТЛОЖЕНО (Phase 3+ — отдельные PR)

### MEDIUM (15 open — старые: аудиты #6–#9)

M2 BASH_DENYLIST `|`, M3 timeout в Docker, M4 transcribe_audio dup, M5 docs `<ul>`, M6 gmail_list_unread, M7 tool_calls `[]`, M8 test_db_manager stub, M9 TUI return type, M10 web3 API mix, M11 AgentStore race, M13 web_scrape dup, M15 auth_provider SQLite, M17 skill_cache keywords, M18 psycopg2 sync pool.

### MEDIUM (22 open — новые: аудит #10)

M1 web/server.py int() на Content-Length, M2 chunked encoding bypass, M3 MCP server path traversal, M4 demo_router CWD-зависимые пути, M5 a2a_server memory_queue, M6 pg_state destructive DROP TABLE, M7 prompt_eval self-bias, M8 asyncio.run в asyncio-тестах, M9 validation.py path issues, M10 pg_state tool_calls=[] → NULL, M11 permissions.py FastAPI coupling, M12 agent_store KeyError, M13 state_db duplicate messages, M14 builder.py race, M15 _set_auth_cookie dead code, M16 duplicate psycopg2-binary req, M17 httpx version drift, M18 demo_router subprocess hang, M19 Caddy not in compose, M20 docker-compose version deprecated, M21 tautological test assertion, M22 empty test stub.

### LOW (13 open — старые: аудиты #6–#9)

L3 double register_tools, L4 dead import orchestrator, L5 vision LLMGateway, L6 /onboarding dead path, L7 entrypoint.sh, **L8 .env key in git (rotate!)**, L9 agent.json vs MODEL_PROFILES, L10 requirements.txt dup, L11 _set_auth_cookie dead, L12 conninfo unused, L13 re import in docs, L15 asyncio.run thread pool, L16 deprecated lifespan.

### LOW (23 open — новые: аудит #10)

L1 agent.py redundant import, L2 orchestrator dead import, L3 asyncio import in method, L4 db_manager conninfo dead, L5 logger.py makedirs crash, L6 session_cache double prefix, L7 quality_metrics ZeroDivision, L8 workflow executor O(n²) logs, L9 duplicate _has_cycle, L10 module-level AgentStore, L11 feedback format shadow, L12 data_tools unused subprocess, L13 server.py unused imports, L14 mcp_server private attr, L15 a2a_server unused request, L16 auth_router circular import, L17 tui.py unused SKILLS_DIRS, L18 skill_cache dead mapping, L19 registry.json missing tool impl, L20 entrypoint.sh ignored flag, L21 .env.example drift, L22 timeout ignored in docker runners, L23 no depends_on for n8n.

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

**Итог #10 (новый аудит):** Независимый аудит 80+ файлов. Обнаружено **65+ новых проблем**, не покрытых предыдущими аудитами. Впервые найдены: command injection в `_run_javascript`, path traversal в `file_tools`, message duplication в `memory_manager`, неатомарный `compress_session`, race condition в `mcp_client_manager`, миграции всегда в SQLite, Docker sandbox не работает в контейнере, `.dockerignore` не защищает от node_modules, missing deps в requirements.txt, дефолтный пароль "admin" в двух местах, живой API-ключ закоммичен. Все найденные проблемы отслежены по цепочке: причина → следствие → impact. Phase 3 backlog расширен: 15→37 MEDIUM, 13→36 LOW.

**Итог #9 (re-audit):** Phase 0–2 fixes **подтверждены**. Gate 46/46 PASS. Manual smoke PASS. CRITICAL/HIGH = 0 open. Phase 3: 17 MEDIUM + 13 LOW.

**Итог #8:** Phase 0–2 закрыли **13 CRITICAL** (11 реальных + 2 false positive), **16 HIGH**. pytest gate: 46/46. Phase 3 — MEDIUM/LOW в backlog.

**Итог #7:** *(исторический)* аудит #7 добавил +6 CRITICAL, +6 HIGH. Основной системный баг — тулы не регистрировались.
