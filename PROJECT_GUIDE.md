# My Agent — Руководство (RU)

> Версия **3.5.3** · 2026-05-31  
> Краткое RU-руководство. Полный индекс: [docs/README.md](docs/README.md).

---

## Обзор

**My Agent** — платформа автономных workflow с multi-agent чатом, визуальным builder и маркетплейсом шаблонов.

| Компонент | Значение |
|-----------|----------|
| Primary LLM | OpenRouter — `openrouter/owl-alpha` (`OPENROUTER_API_KEY`) |
| Fallback | `google/gemini-2.5-flash-preview` (тот же OpenRouter ключ) |
| Опционально | Kimi Code API (`KIMI_API_KEY`) |
| UI | React SPA на `/app/*`, RU i18n |
| БД | PostgreSQL (prod), SQLite (dev без `ENV=production`) |
| Очередь | Redis — rate limits, workflow runs |

**Канонический demo (без логина):** http://127.0.0.1:8020/showcase#playground

---

## Установка

### Docker (рекомендуется)

```bash
cp .env.example .env
# OPENROUTER_API_KEY=sk-or-v1-...   # для live chat
docker compose up -d --build
open http://127.0.0.1:8020/app
```

Порты: **8020** (web), **5437** (PostgreSQL localhost), **6380** (Redis localhost).

### Локально без Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

Frontend: `cd web/frontend && bun run build`.

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

Windows: см. [WINDOWS_LAUNCH.md](WINDOWS_LAUNCH.md).

---

## Web UI

| URL | Описание |
|-----|----------|
| `/showcase#playground` | **Канонический investor demo** (публичный) |
| `/login` | Вход, регистрация, Google OAuth |
| `/app/` | Dashboard |
| `/app/chat` | Чат (Beta — нужен API key для live LLM) |
| `/app/workflows` | Workflow list + builder |
| `/app/marketplace` | 52+ шаблонов, demo-run |
| `/app/settings` | Ключи, billing, agents/knowledge/MCP |
| `/showcase` | 7 вертикальных кейсов + playground |

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
| POST | `/api/demo/run` | Investor demo presets |
| POST | `/api/demo/public/run` | Публичный showcase demo |

Полный список: OpenAPI `http://localhost:8020/docs` (при запущенном сервере).

---

## Агенты

7 профилей в `agents/registry.json`: **universal**, researcher, developer, marketer, data_analyst, slides, docs.

Universal подключает все skills автоматически; остальные — узкоспециализированные.

---

## Навыки (Skills)

33 каталога в `skills/<name>/` (`SKILL.md` + `skill.py`). Регистрация через `register_tools()`.

Примеры: `deep_research`, `browser`, `rag`, `docs`, `slides`, `messaging`, `scheduler`, `git_integration`.

Добавление навыка:

1. `skills/my_skill/SKILL.md` + `skill.py`
2. Подключить в `agents/registry.json` или через UI Settings

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

CI: [.github/workflows/ci.yml](.github/workflows/ci.yml).

---

## Troubleshooting

| Симптом | Решение |
|---------|---------|
| 500 в чате (Docker) | Проверить `OPENROUTER_API_KEY`, пересоздать agent: `docker compose up -d --force-recreate agent` |
| Postgres sessions error | См. раздел 1.1 в [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (исправлено в 3.5.2) |
| `redis: false` в health | Запустить Redis, проверить `REDIS_URL` |
| Порт занят | Docker использует **8020**, не 8000 |
| Demo без ключей | Mock fallback — см. [DEMO.md](DEMO.md) |

Полный список: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## См. также

- [README.md](README.md) — EN quick start
- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура
- [DEPLOYMENT.md](DEPLOYMENT.md) · [SERVER.md](SERVER.md) — деплой
- [DEMO.md](DEMO.md) · [INVESTOR.md](INVESTOR.md) — демо
