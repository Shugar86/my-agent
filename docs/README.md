# Документация My Agent

> Индекс актуальной документации. Версия продукта: **4.0.0** (Agent OS pivot).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, быстрый старт Docker, маршруты UI |
| [AGENTS.md](../AGENTS.md) | AI-агенты / разработчики | Контракт: стек, DoD, git workflow, эскалация |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, troubleshooting |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Agent Preview, showcase, 3-минутный сценарий |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, скрипт встречи |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, паттерны |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, systemd, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, Render/Railway/Fly |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки и решения |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Фазы развития после v4 |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill |
| [.env.example](../.env.example) | Переменные окружения |

---

## Внутреннее (команда / AI-сессии)

Не входят в onboarding — снимок контекста и аудитов.

| Документ | Содержание |
|----------|------------|
| [PROJECT.md](../PROJECT.md) | Mission, immutable core, entry points |
| [STATE.md](../STATE.md) | Текущий статус ветки и блокеры |
| [COCKPIT.md](../COCKPIT.md) | Вайб, аудитории, tone of voice |
| [SPOTLIGHT.md](../SPOTLIGHT.md) | Архитектурные «жемчужины» и риски |
| [TROUBLES.md](../TROUBLES.md) | Аудит багов, gate 60/60, OPEN backlog |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| Порт **8000** в старых заметках | Канонический порт: **8020** |
| `KIMI_API_KEY` как primary LLM | С v4 primary — `OPENROUTER_API_KEY` (Kimi закомментирован в `.env.example`) |
| Narrative «Competitor Intelligence за 90 сек» | Заменён на «AI-оператор для бизнеса за 2 минуты» (v4) |
| `AUDIT_*.md`, `HANDOFF.md` | Удалены; актуальный аудит — [TROUBLES.md](../TROUBLES.md) |
