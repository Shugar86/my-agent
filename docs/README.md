# Документация My Agent

> Индекс актуальной документации. Версия продукта: **4.0.0** (2026-05-28).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, быстрый старт Docker, маршруты UI |
| [AGENTS.md](../AGENTS.md) | AI-агенты, разработчики | Контракт: стек, DoD, git workflow |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, troubleshooting |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Agent preview, showcase, live chat |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, паттерны |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | PR, стиль кода, DoD |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, systemd, мониторинг |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Планирование и состояние

| Документ | Содержание |
|----------|------------|
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Фазы 1–4 после v4 |
| [STATE.md](../STATE.md) | Текущий статус, блокеры, milestone |
| [PROJECT.md](../PROJECT.md) | Immutable core, ключевые решения |
| [TROUBLES.md](../TROUBLES.md) | Аудит багов, gate, OPEN backlog (архив) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill |
| [.env.example](../.env.example) | Переменные окружения |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| `KIMI_API_KEY` как primary LLM | С v4.0 — OpenRouter через профиль `balanced` |
