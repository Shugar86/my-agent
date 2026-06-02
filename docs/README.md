# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.3** (2026-06-02).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, быстрый старт Docker, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, troubleshooting |
| [HANDOFF.md](../HANDOFF.md) | Разработчик / агент | Текущее состояние, checklist, key files |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Windows | CLI/TUI, `setup.bat`, Docker |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, паттерны |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, systemd, мониторинг |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | 33 навыка (`SKILL.md` + `skill.py`) |
| [.env.example](../.env.example) | Переменные окружения |

**LLM по умолчанию:** OpenRouter (`OPENROUTER_API_KEY`, модель `openrouter/owl-alpha` в `config/agent.json`). `KIMI_API_KEY` — опционально для Kimi Code API.

**Данные showcase:** [website/data/showcase.json](../website/data/showcase.json) → монтируется как `/welcome-assets/data/showcase.json` для React (`PublicShowcasePage`).

---

## Исторические материалы (архив)

Не обновляются при каждом релизе — снимок на дату аудита или спринта.

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Общий аудит 2026 |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX/metrics snapshot (3.5.0) |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Завершённая 90-дневная дорожная карта |
| [.planning/](../.planning/) | Внутреннее планирование |

---

## Не использовать / не документация

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| `graphify-out/` | Артефакт анализа кода (Graphify), не часть продукта |
| `AI_SKILLS.md` (удалён) | Сводка в `skills/*/SKILL.md` и [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| Kimi как primary LLM в старых аудитах | С 3.5.2 primary — OpenRouter; см. [CHANGELOG.md](../CHANGELOG.md) |
