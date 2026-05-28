# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.2** (2026-05-28).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, Docker quick start, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, skills, troubleshooting |
| [HANDOFF.md](../HANDOFF.md) | Разработчик / агент | Текущее состояние, чеклисты demo и deploy |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Competitor Intelligence 90s |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои, workflow engine, data stores |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, nginx, бэкапы, systemd |
| [deploy/README.md](../deploy/README.md) | Docker prod, Render/Railway/Fly |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | CLI на Windows (без Docker) |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 навыка) |
| [.env.example](../.env.example) | Переменные окружения |
| [config/models.yaml](../config/models.yaml) | Профили моделей CLI |

---

## Архив и внутреннее

| Путь | Назначение |
|------|------------|
| [docs/archive/](./archive/) | Аудиты и ROADMAP_90_DAYS (снимки) |
| [.planning/](../.planning/) | Внутреннее планирование (не для пользователей) |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг → React SPA — [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| Порт **8000** в старых заметках | Актуальный порт: **8020** |
| `KIMI_API_KEY` как «единственный primary» | С 3.5.2 primary LLM — **OpenRouter** (`OPENROUTER_API_KEY`); Kimi — опциональный fallback |
| `graphify-out/` | Артефакты локального анализа кода, не часть продукта |

**Данные showcase:** [website/data/showcase.json](../website/data/showcase.json) — по-прежнему используется React SPA (`demoFallback.ts`).
