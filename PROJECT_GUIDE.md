# My Agent — Руководство (RU)

> Версия **3.5.2** · 2026-06-12  
> Краткое RU-руководство. Полный индекс: [docs/README.md](docs/README.md).

---

## Обзор

**My Agent** — платформа автономных workflow с multi-agent чатом, визуальным builder и маркетплейсом шаблонов.

| Компонент | Значение |
|-----------|----------|
| Primary LLM | OpenRouter (`OPENROUTER_API_KEY`, `config/agent.json`) |
| Fallback | Gemini через OpenRouter; опционально Kimi (`KIMI_API_KEY`) |
| UI | React SPA на `/app/*`, RU i18n |
| БД | PostgreSQL (prod), SQLite (dev без `ENV=production`) |
| Очередь | Redis — rate limits, workflow runs |

---

## Установка

### Docker (рекомендуется)

```bash
cp .env.example .env
# OPENROUTER_API_KEY=sk-or-v1-...  — для live chat (demo работает без ключей)

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

Frontend: `cd web/frontend && bun install && bun run build`.

Windows: см. [WINDOWS_LAUNCH.md](WINDOWS_LAUNCH.md).

---

## CLI

```bash
python agent.py --help

python agent.py chat --model balanced   # OpenRouter (по умолчанию в prod)
python agent.py serve --port 8020       # web-сервер
python agent.py list-agents
python agent.py test --fast             # pytest без slow/docker
```

В чате: `/help`, `/exit`, `/clear`, `/model`.

Профили моделей: `core/configurator.py` → `MODEL_PROFILES` (`fast`, `balanced`, `smart`, `kimi`, `local`).  
Глобальный default: `config/agent.json`. Файл `config/models.yaml` **не используется** runtime.

---

## Web UI

| URL | Описание |
|-----|----------|
| `/`, `/showcase`, `/demo` | Публичные страницы; канонический demo: `/showcase#playground` |
| `/login` | Вход, регистрация, Google OAuth |
| `/app/` | Dashboard |
| `/app/chat` | Чат (Beta — нужен `OPENROUTER_API_KEY`) |
| `/app/workflows` | Workflow list + builder |
| `/app/marketplace` | Шаблоны, demo-run |
| `/app/settings` | Ключи, billing, agents/knowledge/MCP (tabs) |
| `/app/analytics` | Usage dashboard |
| `/app/onboarding` | 4-step wizard |

Legacy: `/app/agents`, `/app/knowledge`, `/app/mcp` → редирект на `/app/settings?tab=…`.

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
| POST | `/api/demo/public/run` | Public demo (без auth) |

Полный список: OpenAPI `http://localhost:8020/docs` (при запущенном сервере).

---

## Агенты

10 профилей в `agents/registry.json`:

| ID | Назначение |
|----|------------|
| **universal** | Все skills автоматически |
| researcher | Deep research, parsing |
| developer | Code analysis, execution, Git |
| marketer | Slides, social, content |
| data_analyst | CSV, charts, SQL |
| slides | Презентации |
| docs | DOCX, PDF, отчёты |
| media_processor | OCR, audio, video |
| data_engineer | ETL, SQL, pipelines |
| news_monitor | RSS, news digest |

---

## Навыки (Skills)

33 модуля в `skills/<name>/SKILL.md`. Регистрация через `register_tools()` в `skill.py`.

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
| PG sessions error | Fixed в 3.5.2 — см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) §1.1 |

---

## См. также

- [README.md](README.md) — EN quick start
- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектура
- [DEPLOYMENT.md](DEPLOYMENT.md) · [SERVER.md](SERVER.md) — деплой
- [DEMO.md](DEMO.md) · [INVESTOR.md](INVESTOR.md) — демо
