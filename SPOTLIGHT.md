# SPOTLIGHT — my-agent

## Architecture pearls (2-3 files/decisions that make this project tick)

### 1. `web/server.py` — композиционный корень платформы

Файл (~1600 строк) — единая точка сборки всего стека: FastAPI-приложение `app` подключает роутеры (`mcp_router`, `a2a_router`, `workflow_router`, `demo_router`, `auth_router`, `sessions_router`, `teams_router`, `usage_router`) и навешивает цепочку middleware.

**Паттерны:**
- **Lazy-init runtime** — `_init_agent_runtime()` откладывает создание `AgentStore`, `Orchestrator`, `AutoAgentFactory` до первого запроса/startup, чтобы импорт модуля не тянул тяжёлую инициализацию.
- **Слоёная защита** — `AuthMiddleware` (JWT из cookie `access_token`, revoke через Redis `jti`), `redis_rate_limit_middleware` + `RateLimiter` из `core.session_cache`, `slowapi` `Limiter` на эндпоинтах, `limit_request_size` (10 MB).
- **Multi-transport chat** — один и тот же `AgentBuilder` + `LLMGateway` обслуживает `/api/chat`, SSE `/api/chat/stream`, WebSocket `/ws/chat` и коллаб `/ws/room/{room_id}`.
- **Workspace-aware sessions** — `_user_session_id(user_id, raw_sid, workspace_id)` склеивает `workspace_id::user_id::session_id` для мультитенантности через `team_store`.

Startup (`@app.on_event("startup")`) последовательно поднимает Redis, миграции (`run_migrations`), scheduler, users, workflow triggers (`rehydrate_all_triggers`) и consumer очереди (`run_queue.start_consumer`) — типичный «Agent OS» lifecycle.

### 2. `AgentBuilder` + `Orchestrator` — единый способ собрать агента

Паттерн **Fluent Builder** повторяется в трёх entry points:
- `agent.py` → `cmd_run`, CLI через `cli.tui.run_tui`
- `web/server.py` → `chat_endpoint`, `chat_stream`, `ask_endpoint`, WebSocket
- `core/workflow/nodes/agent.py` → `handle_agent_skill`

Цепочка `.set_model().set_role().set_skills().set_tools().set_memory()` — единый контракт между CLI, Web и workflow engine. `Orchestrator.run()` / `run_with_auto_agents()` — оркестрация на уровне web-слоя, workflow-ноды вызывают `agent.run()` напрямую.

### 3. `core/workflow/nodes/agent.py` — мост workflow ↔ agent

**Registry pattern:** `register_node_handler("agent.skill", handle_agent_skill)` через `core.workflow.registry`. Нода `agent.skill` резолвит конфиг через `RunContext.resolve_config()`, подтягивает агента из `AgentStore`, fallback на `"universal"`, и собирает агента с `enable_events(False)` + `enable_compression(True)` — оптимизация для batch/workflow-контекста (без event-stream, с сжатием контекста).

Это ключевое решение: **агент — примитив, workflow — оркестратор примитивов**.

---

## Hidden risks (1-2 places that could bite)

### 1. `/api/ask` без аутентификации (`web/server.py`, ~708–769)

```python
"""No auth required — perfect for integrations and simple usage."""
```

Эндпоинт доступен публично (если не перекрыт `is_public_path` / middleware — [uncertain], но комментарий и отсутствие проверки `user_id` явно указывают на open API). Риск: **неограниченный расход LLM-токенов** + `ResponseCache` может кэшировать ответы между пользователями при одинаковом `question` + `tools`. Rate limit только `60/minute` через slowapi по IP.

### 2. God-file + дублирование middleware (`web/server.py`)

- **Два Prometheus middleware** — `prometheus_middleware` (стр. 133) и `prometheus_metrics_middleware` (стр. 182) оба инкрементируют `REQUEST_COUNT` и `REQUEST_LATENCY`. Вероятно **двойной учёт метрик**.
- **In-memory collab rooms** — `_collab_rooms: Dict[str, List[WebSocket]]` — state теряется при рестарте, не масштабируется на `--workers > 1` (docker-compose явно `--workers 1`, но это хрупкая связка).
- **Legacy + SPA coexistence** — одновременно `_serve_spa_index()` для `/app/*` и отдельные HTML-страницы (`chat.html`, `agents.html`, …) + редиректы в `AuthMiddleware`. Риск рассинхрона UI-маршрутов.

### 3. Дефолтные секреты и exposed port (`docker-compose.yml`)

- `POSTGRES_PASSWORD:-agentpass`, n8n `admin/demo`, Grafana `admin/admin` — дефолты в compose.
- `agent` слушает `0.0.0.0:8020` (внешний доступ), тогда как PG/Redis только на `127.0.0.1`.
- В комментарии захардкожен IP сервера `159.195.31.95` — утечка инфраструктурной информации в репо.

### 4. Разрозненные экземпляры `AgentStore` [uncertain]

`core/workflow/nodes/agent.py` создаёт module-level `_store = AgentStore()`, а `web/server.py` — глобальный `store` через `_init_agent_runtime()`. Если `AgentStore` читает файлы/DB без shared cache — возможна **рассинхронизация конфигов агентов** между web API и workflow runs.

---

## Reuse gold (what could be copied to another project)

| Паттерн | Где | Зачем копировать |
|---------|-----|------------------|
| `get_client_ip()` | `web/server.py:19–27` | Корректный IP за Caddy/nginx (`X-Forwarded-For`, `X-Real-IP`) |
| `_cors_origins()` | `web/server.py:30–43` | Localhost defaults + `CORS_ORIGINS` env, dedupe через `dict.fromkeys` |
| Type-safe i18n | `web/frontend/src/i18n/index.ts` | `NestedKeys<T>` → `I18nKey`, partial EN overlay (`landing`, `narrative`), `localStorage` locale |
| Node handler registry | `core/workflow/nodes/agent.py` | `register_node_handler(type, handler)` — расширяемый plugin graph без if/else |
| Docker Compose profiles | `docker-compose.yml` | `demo` (n8n), `monitoring` (Prometheus/Grafana) — опциональные сервисы без overhead |
| Lazy runtime init | `web/server.py:_init_agent_runtime` | Отложенная инициализация тяжёлых singleton'ов |
| CLI ↔ Web shared config | `agent.py` + `core/configurator.MODEL_PROFILES` | Один источник model profiles для CLI и Settings UI |
| JWT revoke via Redis | `AuthMiddleware` + `redis_client.is_token_revoked(jti)` | Logout с инвалидацией, не только expiry |
| `resolve_env_vars` / `${ENV}` placeholders | `agent.py:_build_model_config`, `core.config` | Конфиги с секретами через env, не в JSON |

---

## Key commits vibe (if git history visible)

История (май 2026, ~25 коммитов) показывает **интенсивный product sprint с audit-driven remediation**:

- **Ритм:** чередование `feat` → `fix(troubles)` → `docs` — типичный цикл «шипим фичу → аудит находит дыры → закрываем CRITICAL/HIGH».
- **Темы:** v3.3 (CEO audit, billing, memory) → v3.4–3.5 (UX sprint, React landing, onboarding funnel) → **v4 Agent OS pivot** (`ea443a6`) → infra hardening (PG, Redis queue, systemd).
- **Стиль сообщений:** conventional commits с scope (`feat(ux)`, `fix(troubles)`, `fix(critical)`), ссылки на `TROUBLES.md` / audit numbers — дисциплина post-mortem.
- **Последний коммит** (`7344bfe`, 2026-05-30): унификация документации (`PROJECT.md`, `STATE.md`, `COCKPIT.md`) — переход от хаотичного R&D к «операционному» формату.
- **Vibe:** solo/small-team, production-minded, demo-ready (investor showcase, OpenRouter fallback, n8n profile), русскоязычный продукт с EN partial i18n.

---

## Questions for the author

1. **`/api/ask` — намеренно публичный?** Если да, планируется ли API key / per-tenant quota поверх IP rate limit? Сейчас это самый очевидный вектор abuse.

2. **Production: systemd или Docker?** В git есть `feat: v3.4 production readiness — systemd, PG, Redis queue` и коммит «VDS prod uses systemd API, not docker agent container». Какой путь canonical — `docker-compose.yml` только для dev/R&D?

3. **`AgentStore` — singleton или per-request?** Module-level `_store` в workflow nodes vs lazy global в `web/server.py` — один источник правды или осознанное разделение? Нужен ли shared cache/invalidate при CRUD через `/api/agents`?

4. **[uncertain] Дублирование Prometheus middleware** — `prometheus_middleware` и `prometheus_metrics_middleware` оба активны. Это баг или один из них legacy?

5. **CLI (`agent.py`) vs Web** — `_get_cli_user()` / `data/cli_user.json` живут параллельно `UserManager` + JWT auth. CLI и Web — разные пользовательские модели навсегда или планируется unification?
