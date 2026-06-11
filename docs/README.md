# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.2** (2026-06-11).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, Docker quick start, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, агенты, skills, API |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Windows | CLI, Docker, `my-agent.bat` |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, LLM gateway |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS runbook, порты **8020**, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, Render/Railway/Fly, мониторинг |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки (chat, Redis, Postgres) |
| [HANDOFF.md](../HANDOFF.md) | Состояние продукта для новой сессии / automation |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 модуля) |
| [.env.example](../.env.example) | Переменные окружения |

### Ключевые факты (синхронизировано с кодом)

| Параметр | Значение |
|----------|----------|
| Primary LLM | **OpenRouter** (`OPENROUTER_API_KEY`, модель `openrouter/owl-alpha` в `config/agent.json`) |
| Fallback LLM | Kimi / Gemini через litellm (`KIMI_API_KEY` опционально) |
| Web-порт | **8020** (не 8000) |
| Агенты | 10 профилей в `agents/registry.json` |
| Skills | 33 каталога в `skills/` |
| Workflow nodes | 21 тип в `core/workflow/models.py` |
| Marketplace | 52+ шаблона (`scripts/seed_workflow_templates.py`) |

---

## Исторические материалы (архив)

Не обновляются при каждом релизе — снимок на дату аудита или спринта.

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Общий аудит 2026 |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX/metrics snapshot (3.5.0) |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Дорожная карта Phase 1–3 (завершена) |
| [.planning/](../.planning/) | Внутреннее планирование |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| `graphify-out/` | Сгенерированные артефакты анализа кода, не документация |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| `AI_SKILLS.md`, `CONTEXT.md` (удалены) | Сводка перенесена в `skills/*/SKILL.md` и [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) |
