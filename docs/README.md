# Документация My Agent

> Индекс актуальной документации. Версия продукта: **4.0.0** (2026-05-28).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, быстрый старт Docker, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, troubleshooting |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Agent preview, showcase, live chat |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Продукт и состояние

| Документ | Содержание |
|----------|------------|
| [PROJECT.md](../PROJECT.md) | Mission, immutable core, ключевые решения |
| [STATE.md](../STATE.md) | Текущий статус, блокеры, последний релиз |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Фазы 1–4, backlog |
| [COCKPIT.md](../COCKPIT.md) | Вайб продукта по слоям (persona, tone) |
| [SPOTLIGHT.md](../SPOTLIGHT.md) | Архитектурные «жемчужины» и скрытые риски |
| [AGENTS.md](../AGENTS.md) | Контракт для AI-агентов (pair-programmer) |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, паттерны |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, systemd, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, Render/Railway/Fly |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки (операционный runbook) |
| [TROUBLES.md](../TROUBLES.md) | Аудит-бэклог и gate-результаты (не runbook) |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Как участвовать в проекте |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill |
| [.env.example](../.env.example) | Переменные окружения |
| [agents/registry.json](../agents/registry.json) | 10 профилей агентов |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| `KIMI_API_KEY` как primary LLM | Удалён в v4; primary — `OPENROUTER_API_KEY` |
| Удалённые `AUDIT_*.md`, `HANDOFF.md` | Контент перенесён в `TROUBLES.md`, `STATE.md`, `SECURITY.md` |
