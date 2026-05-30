# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.3** (2026-05-30).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, Docker quick start, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, skills, API, troubleshooting |
| [HANDOFF.md](../HANDOFF.md) | Новая сессия / automation | Текущее состояние, demo checklist, env |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Windows | CLI / TUI без Docker |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои, workflow engine, data stores |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, systemd, мониторинг |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки (в т.ч. Postgres sessions 3.5.2) |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## LLM и ключи (кратко)

| Переменная | Роль |
|------------|------|
| `OPENROUTER_API_KEY` | **Primary** — live chat, workflow agents (`config/agent.json` → `openrouter/owl-alpha`) |
| `TAVILY_API_KEY` | Веб-поиск в live demo / research (опционально) |
| `KIMI_API_KEY` | Опционально — Kimi Code API, если модель в registry указывает на Kimi |

Без ключей публичное demo на `/showcase#playground` работает на **mock replay**. Подробнее: [.env.example](../.env.example), [PROJECT_GUIDE.md](../PROJECT_GUIDE.md).

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 каталога) |
| [.env.example](../.env.example) | Переменные окружения |
| OpenAPI | `http://localhost:8020/docs` при запущенном сервере |

---

## Архив и внутреннее планирование

| Путь | Содержание |
|------|------------|
| [docs/archive/](archive/) | Аудиты и ROADMAP_90_DAYS (снимки, не обновляются) |
| [.planning/](../.planning/) | ROADMAP, REQUIREMENTS, STATE |

---

## Не использовать / не документация

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| `graphify-out/` | Артефакты конвертации документов (cache), не часть продукта |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| `AI_SKILLS.md` (удалён) | Сводка в `skills/*/SKILL.md` и PROJECT_GUIDE |
