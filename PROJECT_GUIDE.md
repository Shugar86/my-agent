# My Agent — Полная документация

**Версия:** 2.1.0  
**Дата:** 2026-05-24  
**Автор:** AI Development Team  
**Статус:** Production Ready

---

## Содержание

1. [Обзор](#обзор)
2. [Архитектура](#архитектура)
3. [Установка и запуск](#установка-и-запуск)
4. [CLI — Руководство пользователя](#cli--руководство-пользователя)
5. [Web UI](#web-ui)
6. [API Endpoints](#api-endpoints)
7. [Модельные профили](#модельные-профили)
8. [Провайдеры и ключи](#провайдеры-и-ключи)
9. [Агенты](#агенты)
10. [Навыки (Skills)](#навыки-skills)
11. [Инструменты (Tools)](#инструменты-tools)
12. [Безопасность](#безопасность)
13. [Производительность](#производительность)
14. [Тестирование](#тестирование)
15. [Troubleshooting](#troubleshooting)
16. [Разработка](#разработка)

---

## Обзор

**My Agent** — модульная система AI-агентов с поддержкой:

- **27 навыков** и **57 инструментов**
- **10 преднастроенных агентов** (researcher, developer, data_analyst и др.)
- **Dual-provider архитектура** — NeuroAPI (быстрый) + OpenRouter (надёжный fallback)
- **Multi-user** с JWT-аутентификацией
- **Web UI** — dashboard, chat, builder, marketplace
- **CLI** — 13 команд с поддержкой login/logout
- **Docker-only sandbox** для выполнения кода
- **Tavily поиск** — быстрый и стабильный

### Сравнение с конкурентами

| Критерий | My Agent | AutoGPT | Hermes | LangChain | CrewAI |
|----------|----------|---------|--------|-----------|--------|
| Инструменты | **57** | ~20 | 40+ | 100+ | Framework |
| Multi-agent | ✅ | ✅ | ✅ | ✅ | ✅ |
| Web UI | ✅ Full | ✅ | ✅ TUI | ❌ | ❌ |
| Multi-user | ✅ | ⚠️ Beta | ❌ | ❌ | ❌ |
| Russian | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| Code sandbox | ✅ Docker | ✅ | ✅ 7 backends | ❌ | ❌ |
| Fallback provider | ✅ **Dual** | ❌ | ❌ | ❌ | ❌ |

---

## Архитектура

```
my-agent/
├── agent.py              # CLI entry point (13 команд)
├── web/server.py         # FastAPI Web UI (52 endpoint'а)
├── core/                 # 32 модуля ядра
│   ├── runtime.py        # AgentRuntime — async execution loop
│   ├── llm_gateway.py    # LLMGateway — retry + fallback
│   ├── builder.py        # AgentBuilder — fluent pattern
│   ├── skill_cache.py    # Token economy — pre-filter skills
│   ├── auth.py           # JWT + bcrypt + Redis blacklist
│   └── ...
├── skills/               # 28 skill modules
├── tools/                # 22 tool implementations
├── agents/               # 10 agent profiles (registry.json)
├── tests/                # 264 тестов
└── config/               # agent.json, models.yaml, .env.example
```

### Поток выполнения

1. Пользователь → CLI/Web UI
2. AgentBuilder → создаёт AgentRuntime
3. Runtime → LLMGateway (NeuroAPI primary, OpenRouter fallback)
4. LLM решает → вызывать tools или ответить напрямую
5. **Parallel tool execution** — asyncio.gather() для независимых инструментов
6. SkillCache → предфильтрует 57 инструментов до ~10-15 релевантных
7. Ответ → пользователю

---

## Установка и запуск

### Требования

- Python 3.11+ (рекомендуется 3.12-3.14)
- Windows / Linux / macOS
- Docker Desktop (опционально, для sandbox)
- 2 GB RAM минимум

### Быстрый старт

```bash
# 1. Клонирование
git clone <repo> my-agent
cd my-agent

# 2. Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# 3. Зависимости
pip install -r requirements.txt

# 4. Конфигурация API ключей
cp .env.example .env
# Отредактируй .env — добавь свои ключи:
# OPENROUTER_API_KEY=sk-or-v1-...
# NEUROAPI_API_KEY=sk-oK9...
# TAVILY_API_KEY=tvly-dev-...

# 5. Запуск CLI
python agent.py chat --model fast

# 6. Запуск Web UI
python agent.py serve --port 8000
```

### Docker

```bash
docker-compose up --build
# Открой http://localhost:8000
```

---

## CLI — Руководство пользователя

### Доступные команды

| Команда | Описание | Пример |
|---------|----------|--------|
| `login [user]` | Вход в CLI-сессию | `agent login admin` |
| `logout` | Выход из сессии | `agent logout` |
| `chat` | Интерактивный чат | `agent chat --model fast` |
| `run-agent` | Одноразовый запуск | `agent run-agent universal --input "hi"` |
| `run` | Запуск задачи | `agent run research --input "AI news"` |
| `serve` | Web-сервер | `agent serve --port 8000` |
| `status` | Статус системы | `agent status` |
| `services` | Проверка сервисов | `agent services` |
| `logs` | Просмотр логов | `agent logs --follow` |
| `list-agents` | Список агентов | `agent list-agents` |
| `list-skills` | Список навыков | `agent list-skills` |
| `list-tasks` | Список задач | `agent list-tasks` |
| `test` | Запуск тестов | `agent test --fast` |
| `benchmark` | Бенчмарк | `agent benchmark` |
| `init` | Создать задачу | `agent init mytask` |

### Модельные профили CLI

```bash
# Быстрый (neuroapi primary, ~1.5с)
python agent.py chat --model fast

# Сбалансированный (OpenRouter primary, ~6с)
python agent.py chat --model balanced

# Умный (Claude Sonnet, ~8с)
python agent.py chat --model smart

# Локальный (Ollama)
python agent.py chat --model local
```

### Команды в чате

```
/help      — Показать справку
/exit      — Выйти из чата
/clear     — Очистить историю
/model     — Информация о модели
/user      — Текущий пользователь
```

---

## Web UI

### Страницы

| URL | Описание |
|-----|----------|
| `/` | Dashboard — статистика, агенты, quick actions |
| `/chat` | Чат-интерфейс с markdown и подсветкой синтаксиса |
| `/agents` | CRUD управление агентами |
| `/builder` | Визуальный конструктор агентов (drag-and-drop) |
| `/marketplace` | Маркетплейс навыков |
| `/settings` | Настройки API ключей |
| `/knowledge` | База знаний (ChromaDB) |
| `/login` | Авторизация |

### API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/api/chat` | POST | Отправить сообщение (JSON) |
| `/api/chat/stream` | POST | Потоковый ответ (SSE) |
| `/api/agents` | GET/POST | Список / создание агентов |
| `/api/agents/{id}` | GET/PUT/DELETE | CRUD агента |
| `/api/marketplace` | GET | Доступные навыки |
| `/api/schedule` | GET/POST | Планировщик задач |
| `/api/health` | GET | Health check |
| `/metrics` | GET | Prometheus метрики |

---

## Модельные профили

### 4 встроенных профиля

| Профиль | Primary | Fallback | Скорость | Когда использовать |
|---------|---------|----------|----------|-------------------|
| `fast` | neuroapi gpt-5.4-nano | OpenRouter owl-alpha | **~1.5с** | Повседневные задачи, quick answers |
| `balanced` | OpenRouter owl-alpha | neuroapi gpt-5.4-nano | ~6с | Сложные запросы, нужна надёжность |
| `smart` | OpenRouter Claude Sonnet 4 | OpenRouter owl-alpha | ~8с | Глубокий анализ, код, reasoning |
| `local` | Ollama llama3 | — | Local | Без интернета, приватность |

### Настройка кастомного профиля

```json
// config/agent.json
{
  "model": {
    "primary": "openai/gpt-5.4-nano",
    "api_key": "${NEUROAPI_API_KEY}",
    "base_url": "https://neuroapi.host/v1",
    "fallback": "openrouter/owl-alpha",
    "fallback_api_key": "${OPENROUTER_API_KEY}",
    "fallback_base_url": "https://openrouter.ai/api/v1",
    "params": {
      "temperature": 0.7,
      "max_tokens": 8192
    }
  }
}
```

---

## Провайдеры и ключи

### NeuroAPI (Россия)

- **URL:** https://neuroapi.host/v1
- **Модель:** gpt-5.4-nano
- **Скорость:** ~1.5-2с
- **Стоимость:** Бесплатно ($5/месяц квота)
- **Ограничения:** Может перегружаться (6000+ пользователей)
- **Ключ:** Получить на https://neuroapi.host/dashboard

### OpenRouter (Global)

- **URL:** https://openrouter.ai/api/v1
- **Модель:** owl-alpha, Claude, Mistral и др.
- **Скорость:** ~5-9с
- **Стоимость:** Есть бесплатные модели
- **Надёжность:** Высокая, enterprise-grade
- **Ключ:** Получить на https://openrouter.ai/keys

### Tavily (Поиск)

- **URL:** https://api.tavily.com
- **Скорость:** ~0.9-1.5с
- **Стоимость:** Есть free tier
- **Преимущества:** Быстрее DuckDuckGo, стабильный API
- **Ключ:** Получить на https://app.tavily.com

---

## Агенты

### Встроенные агенты (10)

| ID | Название | Иконка | Навыки | Инструменты | Описание |
|----|----------|--------|--------|-------------|----------|
| universal | Universal Assistant | 🤖 | 27 | 57 | Универсальный ассистент со всеми навыками |
| researcher | Researcher | 🔍 | 4 | 7 | Глубокое исследование, поиск, анализ |
| developer | Developer | 💻 | 3 | 7 | Анализ кода, написание, ревью |
| marketer | Marketer | 📢 | 5 | 7 | Маркетинг, контент, аналитика |
| data_analyst | Data Analyst | 📊 | 3 | 7 | Анализ данных, визуализация |
| slides | Slides Agent | 🎨 | 3 | 6 | Создание презентаций |
| docs | Docs Agent | 📄 | 3 | 6 | Генерация документов DOCX/PDF |
| media_processor | Media Processor | 🎬 | 3 | 7 | OCR, аудио, изображения |
| data_engineer | Data Engineer | 🗄️ | 3 | 7 | SQL, базы данных |
| news_monitor | News Monitor | 📰 | 4 | 6 | RSS, email, новости |

### Создание агента

```bash
# Через Web UI: /builder — drag-and-drop навыки
# Через API:
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my_agent",
    "name": "My Agent",
    "icon": "🚀",
    "description": "Custom agent",
    "role": "You are a helpful assistant.",
    "skills": ["research", "code_analysis"],
    "tools": ["web_search", "execute_code"],
    "memory": {"enabled": true}
  }'
```

---

## Навыки (Skills)

### 28 навыков

| Навык | Описание | Инструменты |
|-------|----------|-------------|
| **api_integration** | HTTP API коннектор | api_get, api_post, api_put, api_delete |
| **audio_transcription** | Whisper транскрипция | transcribe_audio, translate_audio |
| **auto_agents** | Авто-создание агентов | spawn_sub_agents, analyze_task |
| **browser** | Браузерная автоматизация | browser_navigate, browser_click, ... |
| **code_analysis** | Анализ кода | file_read, file_write |
| **code_execution** | Выполнение кода | execute_code |
| **data_analyst** | Анализ данных | analyze_csv, create_chart |
| **deep_research** | Глубокое исследование | deep_search, scholar_search |
| **docs** | Генерация документов | create_document, convert_to_format |
| **email** | Отправка email | send_email |
| **git_integration** | Git/GitHub | git_clone, github_list_issues |
| **image_generation** | Генерация изображений | generate_image |
| **messaging** | Telegram, Discord, Slack | send_message |
| **ocr** | OCR для изображений/PDF | ocr_image, ocr_pdf |
| **rag** | Retrieval-Augmented Generation | add_knowledge, search_knowledge |
| **research** | Веб-поиск | web_search, web_scrape |
| **rss_news** | RSS-ленты | parse_rss, fetch_article |
| **scheduler** | Планировщик задач | schedule_task, list_scheduled_tasks |
| **self_dev** | Самомодификация | read_source, write_source |
| **slides** | Презентации | create_presentation, export_pptx |
| **social_media** | Twitter/X | post_tweet, search_tweets |
| **sql_db** | SQLite запросы | query_sqlite, list_tables |
| **template** | Шаблоны | file_write |
| **translation** | Перевод | detect_language, translate_text |
| **vision** | Анализ изображений | analyze_image |
| **web_automation** | Веб-скрапинг | web_search, web_scrape |

### Добавление навыка

1. Создать директорию `skills/my_skill/`
2. Добавить `SKILL.md` — документация
3. Добавить `skill.py` — регистрация инструментов
4. Добавить инструменты в `tools/my_tools.py`
5. Зарегистрировать через `register_tools()`

---

## Инструменты (Tools)

### 22 реализации

Все инструменты регистрируются через `register_tools()` (либо определённый в файле, либо импортированный из навыка).

| Файл | Инструменты | Регистрация |
|------|-------------|-------------|
| api_connector.py | api_get, api_post, api_put, api_delete | def |
| audio_transcription_tools.py | transcribe_audio, translate_audio | import (from skill) |
| auto_agents_tools.py | spawn_sub_agents, analyze_task | def |
| code_tools.py | execute_code | def |
| data_tools.py | analyze_csv, create_chart, run_python | def |
| deep_search_tools.py | deep_search, scholar_search, web_scrape | def |
| docs_tools.py | create_document, convert_to_format | def |
| email_tools.py | send_email | import (from skill) |
| file_tools.py | file_read, file_write | def |
| git_integration_tools.py | git_clone, git_status, github_list_issues | import (from skill) |
| image_generation_tools.py | generate_image, generate_image_variation | import (from skill) |
| mcp_client.py | MCPClient class | def |
| ocr_tools.py | ocr_image, ocr_pdf | import (from skill) |
| rss_news_tools.py | parse_rss, fetch_article | import (from skill) |
| slides_tools.py | create_presentation, export_pptx | def |
| social_media_tools.py | post_tweet, search_tweets | import (from skill) |
| sql_db_tools.py | query_sqlite, list_tables | import (from skill) |
| translation_tools.py | detect_language, translate_text | import (from skill) |
| vector_tools.py | add_knowledge, search_knowledge, ... | def |
| web_tools.py | web_search, web_scrape | def |

---

## Безопасность

### Реализовано

| Слой | Механизм | Статус |
|------|----------|--------|
| Аутентификация | JWT + bcrypt + Redis blacklist | ✅ |
| Авторизация | Role-based (admin/user) | ✅ |
| Rate limiting | slowapi (10-60/min per endpoint) | ✅ |
| Code sandbox | Docker-only (no subprocess fallback) | ✅ |
| Input validation | Path safety, SQL injection prevention | ✅ |
| CORS | Whitelist localhost origins | ✅ |
| Error handling | Generic error messages (no stack leaks) | ✅ |
| Secrets | `.env` + `.agent_secret` (gitignored) | ✅ |

### Docker Sandbox

```python
# core/docker_sandbox.py
DockerSandbox(
    network="none",      # Нет outbound сети
    memory="512m",       # Ограничение памяти
    cpu="1.0",           # Ограничение CPU
    read_only=True,      # Read-only filesystem
    timeout=30           # Таймаут 30с
)
```

---

## Производительность

### Метрики (реальные измерения)

| Операция | Время | Провайдер |
|----------|-------|-----------|
| Простой запрос | **1.5-2.0с** | NeuroAPI |
| Запрос с инструментами | 2.0-4.0с | NeuroAPI |
| Fallback запрос | 5.0-9.0с | OpenRouter |
| Tavily поиск | **0.9-1.5с** | Tavily |
| Параллельные инструменты | ~1.5с суммарно | Async |
| Фильтрация skills | <0.001с | Cache |

### Экономия токенов

- **SkillCache** предфильтрует 57 инструментов → ~10-15 релевантных
- Экономия: **~30% токенов** на контекст
- Кэш паттернов: TTL 1 час, сохраняется в `data/cache/skill_patterns.json`

---

## Тестирование

### Запуск

```bash
# Быстрые тесты (без slow/docker/e2e)
python agent.py test --fast
# или
python -m pytest tests/ -m "not slow and not docker and not postgres and not e2e and not ux" -q

# С coverage
python agent.py test --coverage

# Полный набор
python -m pytest tests/ -q
```

### Статистика

| Метрика | Значение |
|---------|----------|
| Всего тестов | **296** |
| Проходят | **264** |
| Пропущены | 1 (UX без API) |
| Исключены | 31 (slow/docker/postgres/e2e) |
| Падают | **0** |
| Покрытие | ~85% |
| Время | ~35-40с |

---

## Troubleshooting

### "Слишком большая нагрузка" (NeuroAPI)

**Причина:** NeuroAPI перегружен (6000+ пользователей)

**Решение:**
```bash
# Система автоматически переключается на OpenRouter fallback
# Или используй --model balanced:
python agent.py chat --model balanced
```

### Docker not available

**Причина:** Docker Desktop не запущен на Windows

**Решение:**
```bash
# Запустите Docker Desktop
# Или используйте execute_code без Docker (ограниченный режим)
```

### 401 Unauthorized (OpenRouter)

**Причина:** Невалидный API ключ

**Решение:**
```bash
# Проверьте ключ:
echo $OPENROUTER_API_KEY
# Получите новый на https://openrouter.ai/keys
```

### Медленные ответы (>10с)

**Причина:** OpenRouter primary слишком медленный

**Решение:**
```bash
# Переключитесь на fast profile (NeuroAPI primary):
python agent.py chat --model fast
```

### Deprecation warnings

**Причина:** pytest-asyncio использует deprecated API

**Решение:** Безопасно игнорировать. Исправление запланировано на Python 3.16.

---

## Разработка

### Структура core/

| Модуль | Назначение |
|--------|------------|
| runtime.py | Главный цикл выполнения агента |
| llm_gateway.py | Абстракция LLM + retry + fallback |
| builder.py | Fluent Builder для конфигурации |
| skill_cache.py | Кэширование релевантных навыков |
| auth.py | JWT аутентификация |
| docker_sandbox.py | Изолированное выполнение кода |
| db_manager.py | SQLite/PostgreSQL dual mode |
| scheduler_manager.py | APScheduler задачи |

### Добавление инструмента

1. Создать функцию в `tools/my_tool.py`
2. Добавить `register_tools()` и `unregister_tools()`
3. Использовать `@registry.register(...)` декоратор
4. Добавить тесты в `tests/test_my_tool.py`
5. Обновить `agents/registry.json`

### Добавление навыка

1. Создать `skills/my_skill/SKILL.md` — документация
2. Создать `skills/my_skill/skill.py` — регистрация
3. Обновить `agents/registry.json` — добавить в skills
4. Добавить тесты

---

## Лицензия

MIT License — свободное использование, модификация и распространение.

---

**Контакты:**  
- Документация: `README.md`, `ARCHITECTURE.md`, `DEPLOYMENT.md`
- Баг-трекер: GitHub Issues
- Чат поддержки: https://t.me/neuroapihost
