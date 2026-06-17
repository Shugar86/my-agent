# Документация My Agent

> Индекс актуальной документации. Версия продукта: **4.0.0** (2026-06).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, быстрый старт Docker, маршруты UI |
| [AGENTS.md](../AGENTS.md) | AI-агенты, разработчики | Контракт: стек, DoD, git workflow, эскалация |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, troubleshooting |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Agent preview, 3-минутный скрипт |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, showcase verticals |
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
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки и решения |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Дорожная карта (фазы 1–4) |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 навыка) |
| [.env.example](../.env.example) | Переменные окружения |

---

## Аудит и backlog

| Документ | Содержание |
|----------|------------|
| [TROUBLES.md](../TROUBLES.md) | Аудит багов, gate-результаты, OPEN backlog |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| `KIMI_API_KEY` | Удалён в v4; primary LLM — `OPENROUTER_API_KEY` |
