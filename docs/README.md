# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.3** (2026-05-29).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, Docker, маршруты UI, переменные окружения |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, troubleshooting |
| [HANDOFF.md](../HANDOFF.md) | Новая сессия / automation | Demo checklist, ключевые файлы, env |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Windows | CLI и Docker без жёстких путей |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, LLM gateway |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Render, Railway, Fly, prod compose |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 пакета) |
| [.env.example](../.env.example) | Переменные окружения |
| [agents/registry.json](../agents/registry.json) | 10 профилей агентов |
| [config/models.yaml](../config/models.yaml) | Профили моделей CLI |

---

## Архив (исторические снимки)

Не синхронизируются с каждым релизом — см. [docs/archive/README.md](archive/README.md).

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Технический аудит |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX / metrics snapshot |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | 90-дневная дорожная карта |
| [.planning/](../.planning/) | Внутреннее планирование |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html`, `website/showcase.js` | Статический лендинг заменён React SPA — [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| `graphify-out/` | Артефакт анализа кода, не документация |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| `KIMI_API_KEY` как «primary» в старых аудитах | Primary LLM: **OpenRouter** (`OPENROUTER_API_KEY`) |
