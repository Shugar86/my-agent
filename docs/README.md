# Документация My Agent

> Индекс актуальной документации · **v3.5.3** · обновлено 2026-06-04

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, Docker quick start, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, skills, troubleshooting |
| [HANDOFF.md](../HANDOFF.md) | Новая сессия / агент | Текущее состояние продукта, demo checklist |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, data stores |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, systemd, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, Render/Railway/Fly |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Запуск на Windows (CLI + Docker) |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |
| [website/BRAND.md](../website/BRAND.md) | Positioning, CTAs, tone |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 навыка) |
| [.env.example](../.env.example) | Переменные окружения |
| [agents/registry.json](../agents/registry.json) | 10 профилей агентов |
| OpenAPI | `http://localhost:8020/docs` (при запущенном сервере) |

---

## Ключевые факты (v3.5.3)

| Параметр | Значение |
|----------|----------|
| Primary LLM | **OpenRouter** (`OPENROUTER_API_KEY`, модель `openrouter/owl-alpha`) |
| Fallback LLM | Kimi Code API (`KIMI_API_KEY`) — опционально |
| Порт Docker/VDS | **8020** (не 8000) |
| Канонический demo | **`/showcase#playground`** — без login, mock без ключей |
| Skills | 33 каталога в `skills/` |
| Agents | 10 профилей в `agents/registry.json` |
| Marketplace | 52+ шаблона (`scripts/seed_workflow_templates.py`) |

---

## Архив (исторические снимки)

Не обновляются при каждом релизе — только для контекста.

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (v3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Общий аудит 2026 |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX/metrics snapshot (v3.5.0) |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Дорожная карта (Phase 1–3 ✅) |
| [.planning/](../.planning/) | Внутреннее планирование |

---

## Устаревшее — не использовать

| Путь | Причина |
|------|---------|
| `website/*.html` | Заменены React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| Порт **8000** в старых заметках | Актуальный порт: **8020** |
| Kimi как primary LLM в старых аудитах | С v3.5.2 primary — OpenRouter |
