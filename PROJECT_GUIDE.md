# My Agent — Руководство (RU)

> Версия **4.0.0** · 2026-06-16  
> Краткое RU-руководство. Полный индекс: [docs/README.md](docs/README.md).

---

## Обзор

**My Agent** — AI Agent OS: multi-agent чат, визуальный workflow builder и маркетплейс шаблонов. Пользователь описывает задачу текстом — платформа собирает AI-оператора.

| Компонент | Значение |
|-----------|----------|
| Primary LLM | OpenRouter (`OPENROUTER_API_KEY`) через профиль `balanced` |
| Fallback | Free-модели OpenRouter при 429; mock без ключей на публичном demo |
| UI | React SPA: `/` (лендинг), `/app/*` (продукт), RU i18n |
| БД | PostgreSQL (prod), SQLite (dev без `ENV=production`) |
| Очередь | Redis — rate limits, workflow runs, JWT revoke |

---

## Установка

### Docker (рекомендуется)

```bash
cp .env.example .env
# OPENROUTER_API_KEY — для live LLM; demo работает и без ключей (mock)
docker compose up -d --build
open http://127.0.0.1:8020/
```

Порты: **8020** (web), **5437** (PostgreSQL localhost), **6380** (Redis localhost).

### Локально без Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

export DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
export REDIS_URL=redis://127.0.0.1:6380/0

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

Frontend: `cd web/frontend && bun install && bun run build`.

---

## CLI

```bash
python agent.py --help

python agent.py chat --model fast      # быстрый профиль
python agent.py serve --port 8020      # web-сервер
python agent.py list-agents
python agent.py test --fast            # pytest без slow/docker
```

В чате: `/help`, `/exit`, `/clear`, `/model`.

Профили моделей: `config/models.yaml` (`fast`, `balanced`, `smart`, `local`).

---

## Web UI

| URL | Описание |
|-----|----------|
| `/` | Лендинг: hero + live agent preview |
| `/demo` | Agent preview (shortcut) |
| `/showcase` | 7 vertical кейсов (без login) |
| `/login` | Вход, регистрация, Google OAuth |
| `/app/` | Dashboard (chat-first) |
| `/app/chat` | Multi-thread SSE чат |
| `/app/workflows` | Workflow list + visual builder |
| `/app/marketplace` | Шаблоны, demo-run |
| `/app/settings` | Ключи, agents, integrations, MCP |
| `/app/onboarding` | 4-step wizard |

---

## API (основное)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/health` | Health check |
| POST | `/api/login` | JWT cookie |
| POST | `/api/chat` | Сообщение агенту |
| POST | `/api/chat/stream` | SSE stream |
| POST | `/api/demo/public/agent-preview` | Public: генерация оператора из задачи |
| POST | `/api/demo/public/agent-chat` | Public: follow-up с preview-агентом |
| GET/POST | `/api/agents` | CRUD агентов |
| GET | `/api/workflow-templates` | Marketplace |
| POST | `/api/workflows/{id}/run` | Запуск workflow |

Полный список: OpenAPI `http://localhost:8020/docs` (при запущенном сервере).

---

## Агенты

10 профилей в `agents/registry.json`:

`universal`, `researcher`, `developer`, `marketer`, `data_analyst`, `slides`, `docs`, `media_processor`, `data_engineer`, `news_monitor`.

Universal подключает все skills автоматически; остальные — узкоспециализированные. Все используют `model: "balanced"` → OpenRouter.

---

## Навыки (Skills)

33 навыка в `skills/<name>/` (документация в `SKILL.md`). Регистрация через `register_tools()` в `skill.py`.

Примеры: `deep_research`, `browser`, `rag`, `docs`, `slides`, `messaging`, `scheduler`, `code_execution`, `ocr`, `vision`.

Добавление навыка:

1. `skills/my_skill/SKILL.md` + `skill.py`
2. Подключить в `agents/registry.json` или через UI Settings

---

## Безопасность

- JWT в httpOnly cookie; публичные пути — `web/security.py` → `is_public_path()`
- Rate limits через Redis + slowapi
- `self_dev` отключён при `ENV=production`
- Sandbox кода: Docker (`core/docker_sandbox.py`)
- `AGENT_PASSWORD` ≥ 12 символов в production

Подробнее: [SECURITY.md](SECURITY.md).

---

## Тестирование

```bash
pytest tests/test_code_tools.py tests/test_file_tools.py \
       tests/test_security_improvements.py tests/test_async_utils.py \
       tests/test_db_manager.py tests/test_production_hardening.py \
       tests/test_all.py::test_memory_manager -q

bash scripts/check-secrets.sh
```

E2E: `cd web/frontend && bun run test:e2e` (сервер на `:8020`).

---

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| 500 в чате | Проверить `OPENROUTER_API_KEY`, `DATABASE_URL`, перезапустить сервер |
| 503 на agent-preview | Нет `OPENROUTER_API_KEY` — ожидаемо; UI покажет mock |
| `redis: false` в health | Запустить Redis, проверить `REDIS_URL` |
| Порт занят | Docker использует **8020**, не 8000 |
| Demo без ключей | Mock fallback — см. [DEMO.md](DEMO.md) |

Полный список: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## См. также

- [README.md](README.md) — обзор и quick start
- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура
- [DEPLOYMENT.md](DEPLOYMENT.md) · [SERVER.md](SERVER.md) — деплой
- [DEMO.md](DEMO.md) · [INVESTOR.md](INVESTOR.md) — демо
- [AGENTS.md](AGENTS.md) — контракт для AI-агентов
