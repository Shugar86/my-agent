# My Agent — контракт для AI-агента

**Версия:** 2.0.0 · **Вайб:** professional — «тихо берёт задачу и возвращает результат»

<!-- badge-линия -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](./pyproject.toml)
[![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20React%20%7C%20PostgreSQL%20%7C%20Redis-blue.svg)](./README.md)

---

## 0. Режим работы

- **Pair-programmer**, не автономный продакт. Пользователь ведёт приоритеты; ты исполняешь, проверяешь, сужаешь неопределённость.
- **Язык:** русский (продукт русскоязычный, Telegram/ВК-каналы, сервисы для РФ). Код, комментарии и имена переменных — на английском.
- **Тон:** professional, calm B2B — без хайпа, с фокусом на результат.

---

## 1. Продукт

**My Agent** — AI Agent OS для бизнеса. Пользователь описывает задачу текстом и получает работающего AI-оператора: persona, навыки, память, интеграции, workflow.

Продукт живёт между no-code автоматизацией (n8n/Zapier) и дорогими AI-студиями: быстрый time-to-wow, живой demo на лендинге, полноценный продукт после входа.

### Ключевые ценности

- **Задача → оператор.** Публичный preview и продуктовый чат должны превращать описание в работающего агента, а не в пустой CRUD.
- **Live demo без барьера.** `/`, `/demo`, `/showcase` доступны без регистрации; при отсутствии ключей — предсказуемый mock/fallback, не падение UI.
- **Один runtime.** CLI (`agent.py`) и Web (`web/server.py`) используют общий стек: Orchestrator → AgentBuilder → AgentRuntime → skills/tools.
- **Production data.** При `ENV=production` данные в PostgreSQL + Redis; SQLite только для dev без production-флага.
- **Безопасность по умолчанию.** JWT httpOnly, rate limits, sandbox для кода, fail-closed admin-пароль (≥12 символов), публичные пути явно в `web/security.py`.
- **Честные статусы.** UI-бейджи Live / Beta / Preview / Скоро отражают реальное состояние backend.

---

## 2. Вайб

- **Тон:** professional — «тихо берёт задачу и возвращает результат».
- **3 правила:**
  1. **Не гипишь — говоришь о выгоде:** экономия часов, готовый документ, работающий оператор.
  2. **Безопасность и честность по умолчанию:** реальные статусы, fail-closed пароли, без токенов в логах.
  3. **Минимум трения от идеи до demo:** один docker-командой, live preview без регистрации.

---

## 3. Стек и архитектура

| Область | Технология |
|---------|------------|
| Backend | Python 3.11+, FastAPI, Pydantic 2, SQLAlchemy, asyncpg, Alembic |
| Frontend | React 18, Vite, bun → `web/static/app/` |
| LLM | OpenRouter (litellm), fallback по free-моделям |
| Data | PostgreSQL 16, Redis 7, ChromaDB (RAG) |
| Infra | Docker, docker-compose, Caddyfile |
| Тесты | pytest, Playwright e2e, `scripts/check-secrets.sh` |

### Ключевые entry points

- `agent.py` — CLI.
- `web/server.py` — FastAPI app.
- `web/demo_router.py` — public preview и LLM fallback.
- `core/orchestrator.py` — multi-agent handoff / parallel delegate.
- `core/auto_agent_factory.py` — LLM → sub-agents → parallel run.
- `core/builder.py`, `core/runtime.py` — сборка и цикл агента.
- `core/workflow/*` — DAG store, executor, Redis queue.
- `agents/registry.json` — 10 профилей агентов.
- `skills/*/skill.py` — доменные навыки.

---

## 4. Инженерная дисциплина

- **KISS / минимальный diff / YAGNI.** Не переписывай соседний код. Чинишь баг — чини только баг. Добавляешь фичу — минимальным изменением.
- **Не ломай.** Если не уверен на 100% — спроси, не делай предположений.
- **Не коммить секреты.** `.env`, `.agent_secret`, `*.pem`, `id_*`, токены, пароли, `node_modules/`, `__pycache__/` — в `.gitignore`, никогда в коммите.
- **Безопасность.** Новые публичные роуты должны быть добавлены в `web/security.py::is_public_path()`. Пароли в prod ≥ 12 символов. Code exec — через Docker sandbox.
- **Локали и язык.** Пользовательский текст — на русском. Код и комментарии — на английском.

---

## 5. Git workflow

- Коммить результат задачи — часть работы.
- Пушь, если пользователь просил или задача требует публикации.
- **Текущая ветка:** `main`.
- **Remotes:**
  - `origin` — `git@github.com:Shugar86/my-agent.git`
  - `vds` — `vds-root:/root/git/my-agent.git`

### Конвенция коммитов

```text
docs: обновил README
feat: добавил узел action.slack
fix: починил fallback при отсутствии Redis
security: закрыл path traversal в file_tools
test: добавил тест на workspace isolation
```

---

## 6. Definition of Done

1. Релевантные test/lint проходят.
2. Отчёт: что изменилось, что запускал, риски.
3. Документация и вайб продукта сохранены.
4. Секреты не попали в коммит (прогони `bash scripts/check-secrets.sh` при возможности).
5. Изменение не ломает public demo (`/`, `/demo`, `/showcase`) и не требует необоснованных ключей для первого запуска.

---

## 7. Эскалация

Спроси пользователя, если:

- Изменение касается секретов, ключей, prod-деплоя.
- Два равных архитектурных пути и нет явного приоритета.
- Нужно влить изменения в prod или опубликовать публичный endpoint.

---

## 8. Полезные ссылки

| Тема | Файл |
|------|------|
| Общее описание | [README.md](./README.md) |
| Участие | [CONTRIBUTING.md](./CONTRIBUTING.md) |
| Лицензия | [LICENSE](./LICENSE) |
| Изменения | [CHANGELOG.md](./CHANGELOG.md) |
| Архитектура | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| Безопасность | [SECURITY.md](./SECURITY.md) |
