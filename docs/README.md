# Документация My Agent

> Индекс актуальной документации. Версия продукта: **4.0.0** (Agent OS pivot, 2026-05-28).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, быстрый старт Docker, маршруты UI, env |
| [AGENTS.md](../AGENTS.md) | AI-агенты / разработчики | Контракт: стек, DoD, git workflow, эскалация |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Контрибьюторы | PR, стиль кода, тесты, check-secrets |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, API, troubleshooting |

---

## Продукт и демо

| Документ | Содержание |
|----------|------------|
| [DEMO.md](../DEMO.md) | Сценарий демо: agent preview, showcase, chat |
| [INVESTOR.md](../INVESTOR.md) | URL, env, 3-минутный питч-скрипт |
| [website/BRAND.md](../website/BRAND.md) | Positioning, CTAs, tone, FeatureTag |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Фазы 1–4 после v4 |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, data stores |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS runbook, порты, systemd, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, monitoring |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки и решения |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 навыка) |
| [agents/registry.json](../agents/registry.json) | 10 профилей агентов |
| [.env.example](../.env.example) | Переменные окружения |

---

## Внутренние заметки (maintainers)

Не обязательны для onboarding — снимок контекста для сессий и автоматизаций.

| Документ | Содержание |
|----------|------------|
| [PROJECT.md](../PROJECT.md) | Immutable core, key decisions, health checks |
| [STATE.md](../STATE.md) | Текущий статус, блокеры, последний milestone |
| [COCKPIT.md](../COCKPIT.md) | Vibe / tone по слоям продукта |
| [SPOTLIGHT.md](../SPOTLIGHT.md) | Архитектурные «жемчужины» и скрытые риски |
| [TROUBLES.md](../TROUBLES.md) | Аудит 2026-05-27, gate 60/60, OPEN backlog (архив) |

---

## Устаревшее — не использовать

| Путь / тема | Причина |
|-------------|---------|
| `website/*.html` | Статический лендинг заменён React SPA (`/`, `/app/*`) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в React |
| Порт **8000** в старых заметках | Канонический порт: **8020** |
| `KIMI_API_KEY` / Kimi provider | Удалён в v4; primary LLM — **OpenRouter** (`OPENROUTER_API_KEY`) |
| Narrative «Competitor Intelligence за 90 сек» | Заменён на «AI-оператор за 2 минуты» (agent preview) |
