# Документация My Agent

> Индекс актуальной документации · продукт **3.5.2** · обновление docs **2026-06-01**

**Primary LLM:** OpenRouter (`OPENROUTER_API_KEY`, модель в `config/agent.json`).  
**Опционально:** Kimi (`KIMI_API_KEY`) для отдельных профилей в `agents/registry.json`.  
**Порт по умолчанию:** **8020** (Docker / VDS).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, Docker quick start, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, skills, troubleshooting |
| [HANDOFF.md](../HANDOFF.md) | Новая сессия / агент | Текущее состояние продукта, чеклисты |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Competitor Intelligence 90s |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs (статический сайт deprecated) |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои, workflow engine, data stores |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, systemd, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Render / Railway / Fly / prod compose |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Запуск на Windows (CLI / bat) |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | CI: pytest + frontend build |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 навыка) |
| [config/agent.json](../config/agent.json) | Primary model + API routing |
| [.env.example](../.env.example) | Переменные окружения |

`config/models.yaml` — **не используется runtime** (deprecated, только справка).

---

## Архив (исторические снимки)

[docs/archive/](archive/) — аудиты и roadmap, не синхронизируются с каждым релизом.

Внутреннее планирование: [.planning/](../.planning/).

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Заменён React SPA — [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| `graphify-out/` | Сгенерированный граф кода (dev artifact), не часть продукта |
| Порт **8000** в старых заметках | Актуальный: **8020** |
| `AI_SKILLS.md` | Удалён → `skills/*/SKILL.md` + PROJECT_GUIDE |
