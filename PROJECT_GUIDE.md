# My Agent — Руководство (RU)

> Версия **3.5.3** · 2026-06-06  
> Краткое RU-руководство. Полный индекс: [docs/README.md](docs/README.md).

---

## Обзор

**My Agent** — платформа автономных workflow с multi-agent чатом, визуальным builder и маркетплейсом шаблонов.

| Компонент | Значение |
|-----------|----------|
| Primary LLM | OpenRouter (`OPENROUTER_API_KEY`, профиль `balanced` → `openrouter/owl-alpha`) |
| Альтернатива | Kimi Code API (`KIMI_API_KEY`, профиль `kimi`) |
| Веб-поиск | Tavily (`TAVILY_API_KEY`) для live demo и research |
| UI | React SPA на `/app/*`, RU i18n |
| БД | PostgreSQL (prod), SQLite (dev без `ENV=production`) |
| Очередь | Redis — rate limits, workflow runs |

Конфигурация модели по умолчанию: `config/agent.json`. Профили CLI: `core/configurator.py` → `MODEL_PROFILES`.

---

## Установка

### Docker (рекомендуется)

```bash
cp .env.example .env
# OPENROUTER_API_KEY=sk-or-v1-...  (опционально для live chat)
docker compose up -d --build
open http://127.0.0.1:8020/showcase#playground
```

Порты: **8020** (web), **5437** (PostgreSQL localhost), **6380** (Redis localhost).

### Локально без Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

export DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
export REDIS_URL=redis://127.0.0.1:6380/0

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

Frontend: `cd web/frontend && bun run build`.

Windows: см. [WINDOWS_LAUNCH.md](WINDOWS_LAUNCH.md).

---

## CLI

```bash
python agent.py --help

python agent.py chat --model balanced   # OpenRouter (по умолчанию в registry)
python agent.py chat --model fast       # быстрый профиль
python agent.py serve --port 8020       # web-сервер
python agent.py list-agents
python agent.py test --fast             # pytest без slow/docker
```

В чате: `/help`, `/exit`, `/clear`, `/model`.

Профили моделей: `core/configurator.py` (`fast`, `balanced`, `smart`, `kimi`, `local`).

---

## Web UI

| URL | Описание |
|-----|----------|
| `/showcase#playground` | Канонический public demo (без login) |
| `/login` | Вход, регистрация, Google OAuth |
| `/app/` | Dashboard |
| `/app/chat` | Чат (Beta — нужен `OPENROUTER_API_KEY` для live) |
| `/app/workflows` | Workflow list + builder |
| `/app/marketplace` | 52 шаблона, demo-run |
| `/app/settings` | Ключи, billing, agents/knowledge/MCP (tabs) |
| `/app/onboarding` | 4-step wizard |

Редиректы: `/app/agents` → `settings?tab=agents`, `/welcome` → `/`.

---

## API (основное)

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/health` | Health check |
| POST | `/api/login` | JWT cookie |
| POST | `/api/chat` | Сообщение агенту |
| POST | `/api/chat/stream` | SSE stream |
| GET/POST | `/api/agents` | CRUD агентов |
| GET | `/api/workflow-templates` | Marketplace |
| POST | `/api/workflows/{id}/run` | Запуск workflow |
| POST | `/api/demo/public/run` | Public investor demo |

Полный список: OpenAPI `http://localhost:8020/docs` (при запущенном сервере).

---

## Агенты

7 профилей в `agents/registry.json`: **universal**, researcher, developer, marketer, data_analyst, slides, docs.

Universal подключает все skills автоматически; остальные — узкоспециализированные.

---

## Навыки (Skills)

33 каталога в `skills/<name>/SKILL.md`. Регистрация через `register_tools()` в `skill.py`.

Примеры: `deep_research`, `browser`, `rag`, `docs`, `slides`, `messaging`, `scheduler`, `git_integration`.

Добавление навыка:

1. `skills/my_skill/SKILL.md` + `skill.py`
2. Подключить в `agents/registry.json` или через UI Settings → Agents

---

## Безопасность

- JWT в httpOnly cookie; публичные пути — landing, GET marketplace, demo public API
- Rate limits через Redis (`web/security.py`)
- `self_dev` отключён при `ENV=production`
- Sandbox кода: Docker (`core/docker_sandbox.py`)

Подробнее: [SECURITY.md](SECURITY.md).

---

## Тестирование

```bash
python -m pytest tests/ -q
python -m pytest tests/ -m "not slow and not docker and not e2e" -q   # быстрый набор
```

E2E: `cd web/frontend && bun run test:e2e` (сервер на `:8020`).

---

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| 500 в чате | Проверить `OPENROUTER_API_KEY`, перезапустить сервер |
| `redis: false` в health | Запустить Redis, проверить `REDIS_URL` |
| Порт занят | `docker compose` использует **8020**, не 8000 |
| Demo без ключей | Mock fallback — см. [DEMO.md](DEMO.md) |
| Postgres sessions crash | Lazy pool + auto-migration — см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) §1.1 |

Полный список: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## См. также

- [README.md](README.md) — EN quick start
- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура
- [DEPLOYMENT.md](DEPLOYMENT.md) · [SERVER.md](SERVER.md) — деплой
- [DEMO.md](DEMO.md) · [INVESTOR.md](INVESTOR.md) — демо
