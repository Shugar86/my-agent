# Документация My Agent

> Индекс актуальной документации. Версия продукта: **4.0.0** (2026-05-28).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, быстрый старт Docker, маршруты UI |
| [AGENTS.md](../AGENTS.md) | AI-агенты, контрибьюторы | Контракт: стек, DoD, git workflow |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, troubleshooting |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий live demo, agent preview |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, tone |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, паттерны |
| [PROJECT.md](../PROJECT.md) | Immutable core: mission, принципы, entry points |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, Render, Railway, Fly.io |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки и решения |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Текущий roadmap (Phase 1–4) |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill |
| [.env.example](../.env.example) | Переменные окружения |

---

## Инженерный аудит (архив)

Снимок на дату аудита; не обновляется при каждом релизе.

| Файл | Тема |
|------|------|
| [TROUBLES.md](../TROUBLES.md) | Re-audit gate 60/60, OPEN backlog |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| `KIMI_API_KEY` как primary LLM | С v4.0.0 primary — `OPENROUTER_API_KEY` |
