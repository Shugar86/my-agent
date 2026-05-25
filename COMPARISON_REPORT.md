# СУПЕР ТЕСТЫ + СРАВНЕНИЕ С АНАЛОГАМИ

**Дата:** 2026-05-23  
**Проект:** My Agent (C:\Users\Тема\Desktop\moy agent\my-agent)  
**Референсы:** [Hermes Agent](https://github.com/NousResearch/hermes-agent) (v0.14.0) · [OpenCode](https://github.com/anomalyco/opencode) (v1.15.10)

---

## 1. РЕЗУЛЬТАТЫ СУПЕР ТЕСТОВ

```
✅ Core (test_all)         — 12/12 passed
✅ Skills/Builder          — 6/6  passed
✅ Integration             — 14/14 passed
✅ Production              — 6/6  passed
═══════════════════════════════════════
✅ ALL 38 TESTS PASSED     — 100%
```

**Бэкенд:** PostgreSQL 16 (localhost:5432)  
**Все зависимости:** 24 пакета  
**Общее покрытие:** agent_store, auth, auto_agent_factory, builder, config, context_compressor, event_bus, iteration_budget, llm_gateway, logging_setup, mcp_manager, memory_manager, orchestrator, pg_state, plugin_manager, retry_utils, runtime, skill_loader, state_db, sub_agents, tool_registry, user_manager, vector_db (23 модуля)

---

## 2. СРАВНИТЕЛЬНАЯ ТАБЛИЦА

| Характеристика | **My Agent** | **Hermes Agent** (Nous Research) | **OpenCode** (anomalyco) |
|---|---|---|---|
| **Язык** | Python 3.14 | Python ≥3.11 | TypeScript (65.8%) |
| **Размер кода** | ~12 748 строк | ~200 000–280 000 | ~450 000–530 000 |
| **Файлов** | ~109 | ~600–700 | ~3 000+ |
| **Тестов** | 38 | ~3 000+ | ~несколько тысяч |
| **Архитектура** | Modular (FastAPI + Web UI) | Modular (CLI + Gateway + ACP) | Monorepo (TUI + Web + Desktop) |
| **LLM провайдеров** | 1 (OpenRouter) | 18+ | 20+ |
| **База данных** | PostgreSQL + SQLite | SQLite (FTS5) | SQLite (Drizzle ORM) |
| **Multi-user** | ✅ JWT + PostgreSQL | ❌ Single-user | ❌ Single-user (local-first) |
| **RAG / Vector DB** | ✅ ChromaDB | ❌ | ❌ |
| **MCP серверов** | 12 (1 enabled) | MCP client | MCP server + client |
| **Web UI** | ✅ FastAPI + HTML/JS | ✅ Dashboard (FastAPI) | ✅ SolidJS + Electron |
| **Streaming SSE** | ✅ | ✅ | ✅ |
| **Slash-команды** | ✅ (6 команд) | ✅ (22 команды) | ✅ |
| **Messaging Gateway** | ❌ | ✅ 20 платформ | ❌ (только Slack) |
| **Terminal UI** | ❌ (CLI + Web) | ✅ (prompt_toolkit) | ✅ SolidJS opentui |
| **Sandbox/Изоляция** | ❌ (exec/subprocess) | ✅ 7 terminal backends | ❌ (permission UX) |
| **Self-improving skills** | ❌ | ✅ | ❌ |
| **Plugin система** | ✅ PluginManager | ✅ PluginManager | ✅ @opencode-ai/plugin |
| **Knowledge Graph** | ✅ Graphify | ❌ | ❌ |
| **Session Sharing** | ❌ | ❌ | ✅ |
| **Cloud Sync** | ❌ | ❌ | ✅ |
| **Docker** | ✅ | ✅ | ✅ (Alpine) |
| **IDE Integration** | ❌ | ✅ ACP (VS Code, Zed, JB) | ✅ VS Code + Zed + ACP |
| **Desktop App** | ❌ | ❌ | ✅ Electron (BETA) |
---

## 3. ПОКРЫТИЕ ФУНКЦИОНАЛА (Radar Chart)

```
                    ═══ My Agent ····· Hermes Agent  ─── OpenCode
                  Мультиязычность
                       │
                 Messaging ─┤─ RAG / Vector DB
                       │   │
               Kanban ─┤   │   ├─ Multi-user
                       │   │   │
           Self-improving ─┤   │   │   ├─ MCP
                       │   │   │   │
            Plugin System ─┤   │   │   │   ├─ Streaming
                       │   │   │   │   │
         Terminal UI ─┤   │   │   │   │   ├─ Web UI
                       │   │   │   │   │   │
           Desktop App ─┤   │   │   │   │   │   ├─ CLI
                       │   │   │   │   │   │   │
         IDE Integration ─┤   │   │   │   │   │   │   ├─ Docker
                       │   │   │   │   │   │   │   │
         Sandbox/Security ─┤   │   │   │   │   │   │   │   ├─ Slash Commands
                       │   │   │   │   │   │   │   │   │
         ═══════════════╧═══╧═══╧═══╧═══╧═══╧═══╧═══╧═══╧═══
```

---

## 4. ДЕТАЛЬНЫЙ АНАЛИЗ РАЗЛИЧИЙ

### 4.1 Что My Agent делает ЛУЧШЕ

| Фича | Почему |
|------|--------|
| **Multi-user + JWT** | Единственный из трёх с полноценной multi-user архитектурой. Hermes и OpenCode — single-user. |
| **RAG / Vector DB** | ChromaDB с семантическим поиском на русском. Ни Hermes (нет векторов), ни OpenCode (нет векторов) этого не имеют. |
| **PostgreSQL** | Production-ready БД, async драйвер. Hermes и OpenCode используют только SQLite. |
| **Rate Limiting** | slowapi на всех 28 эндпоинтах. |
| **Knowledge Graph** | Graphify — визуализация зависимостей. |
| **Docker Compose** | 5 сервисов (Caddy, app, postgres, redis, worker). |
| **Session Isolation** | user_id::session_id prefix. |
| **Скиллы с Python-модулями** | Загрузка skill.py с auto-register/unregister. |

### 4.2 Чего не хватает vs Hermes

| Фича Hermes | Impact | Сложность |
|-------------|--------|-----------|
| **Messaging Gateway** (20 platforms) | Medium | HIGH |
| **Terminal backends** (Docker/SSH/Modal) | HIGH | HIGH |
| **Self-improving skills** | Medium | VERY HIGH |
| **Kanban project management** | Medium | MEDIUM |
| **Cron scheduler** | Medium | MEDIUM |
| **30+ инструментов** (browser, image gen, etc.) | HIGH | MEDIUM |
| **FTS5 full-text cross-session search** | Medium | LOW (уже есть StateDB FTS5) |
| **Approvеd gate (опасные команды)** | HIGH | LOW |
| **Output redaction** | Medium | LOW |

### 4.3 Чего не хватает vs OpenCode

| Фича OpenCode | Impact | Сложность |
|---------------|--------|-----------|
| **Dual-agent (build/plan)** | HIGH | MEDIUM |
| **LSP integration** | Medium | HIGH |
| **Session sharing / sync** | Medium | HIGH |
| **Desktop app (Electron)** | Medium | HIGH |
| **20+ LLM providers** | HIGH | MEDIUM |
| **Headless server mode** | Medium | LOW (уже есть) |
| **Code patching/diff preview** | HIGH | MEDIUM |
| **Snapshot/restore sessions** | Medium | MEDIUM |

---

## 5. КЛЮЧЕВЫЕ МЕТРИКИ

| Метрика | My Agent | Hermes Agent | OpenCode |
|---------|----------|--------------|----------|
| **Возраст проекта** | ~6 мес | ~2 года | ~1.5 года |
| **Stars** | — | ~164 000 | ~164 000 |
| **Commits** | ~350 | ~9 278 | ~13 339 |
| **Releases** | — | ~25 | ~811 |
| **Размер команды** | 1 dev | ~15+ devs | ~30+ devs |
| **Время тестов** | 10-15s | ~30-60 min | ~10-30 min |
| **LOC / $ стоимости** | ~12K / $0 | ~250K / $$$ | ~500K / $$$$ |

---

## 6. ВЫВОД ПО ПОЗИЦИОНИРОВАНИЮ

**My Agent — это уникальное решение в своей нише:**

- ✅ **Единственный с multi-user** — подходит для команд, enterprise, семейного использования
- ✅ **Единственный с RAG** — подходит для knowledge management, QnA по документам
- ✅ **Единственный с PostgreSQL** — production-ready, масштабируется
- ❌ **Нет sandbox** — самый слабый по безопасности среди трёх (exec/subprocess без изоляции)
- ❌ **Только 1 LLM провайдер** — риск vendor lock-in
- ❌ **Нет messaging gateway** — не подходит для chat-ботов

**Рекомендованный план развития (по приоритету):**

1. 🔴 **Sandbox/Безопасность** — Docker-изоляция subprocess/exec (догнать Hermes)
2. 🔴 **Multi-LLM провайдеры** — Anthropic, Google, локальные модели (догнать OpenCode)
3. 🟡 **Dual-agent режим** — plan-агент для анализа перед действиями (догнать OpenCode)
4. 🟡 **Approval gate** — подтверждение опасных операций (догнать Hermes)
5. 🟡 **Code patching** — diff-режим для файловых изменений (догнать OpenCode)
6. 🔵 **FTS5 cross-session search** — уже частично есть, доработать UX
7. 🔵 **Messaging Gateway** — Telegram, Discord (выйти в новую нишу)

На данный момент **My Agent занимает уникальную нишу**: multi-user AI агент с RAG и PostgreSQL — **такого нет ни у Hermes, ни у OpenCode.**
