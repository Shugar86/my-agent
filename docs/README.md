# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.2** (2026-06-12).

**Ключевые факты:** порт **8020** · primary LLM — **OpenRouter** (`OPENROUTER_API_KEY`) · demo без ключей через mock fallback.

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, быстрый старт Docker, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, troubleshooting |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Windows | CLI и Docker на Windows |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, паттерны |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, Render/Railway/Fly |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки |
| [HANDOFF.md](../HANDOFF.md) | Состояние продукта для новой сессии |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [config/agent.json](../config/agent.json) | Primary LLM и fallback |
| [core/configurator.py](../core/configurator.py) | Профили моделей (`fast`, `balanced`, `smart`, `kimi`) |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 модуля) |
| [agents/registry.json](../agents/registry.json) | 10 профилей агентов |
| [.env.example](../.env.example) | Переменные окружения |

> `config/models.yaml` помечен как **deprecated** — runtime его не загружает.

---

## Исторические материалы (архив)

Не обновляются при каждом релизе — снимок на дату аудита или спринта.

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Общий аудит 2026 |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX/metrics snapshot (3.5.0) |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Завершённый 90-дневный roadmap (May 2026) |
| [.planning/](../.planning/) | Внутреннее планирование |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| `graphify-out/` | Сгенерированные артефакты анализа кода, не документация |
| `config/models.yaml` | Deprecated; см. `config/agent.json` |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| `/app/agents`, `/app/knowledge`, `/app/mcp` | Редирект на `/app/settings?tab=…` |
