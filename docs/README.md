# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.3** (2026-06-03).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, Docker :8020, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, skills, troubleshooting |
| [HANDOFF.md](../HANDOFF.md) | Разработчик / automation | Текущее состояние, env, demo checklist |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

**Канонический demo (без login):** `http://localhost:8020/showcase#playground`

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои, workflow engine, LLM gateway |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, nginx, бэкапы, systemd |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, мониторинг |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Запуск на Windows (CLI / Docker) |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 каталога) |
| [config/agent.json](../config/agent.json) | Primary LLM и fallback |
| [.env.example](../.env.example) | Переменные окружения |

---

## Планирование (внутреннее)

| Путь | Назначение |
|------|------------|
| [.planning/ROADMAP.md](../.planning/ROADMAP.md) | Актуальная дорожная карта по фазам |
| [.planning/PROJECT.md](../.planning/PROJECT.md) | Контекст продукта |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Снимок 90-дневного плана (май 2026) |

---

## Архив (аудиты, не обновляются каждый релиз)

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Общий аудит 2026 |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX/metrics snapshot (3.5.0) |

---

## Не использовать / не путать с продуктовой докой

| Путь | Причина |
|------|---------|
| `website/*.html` | Заменены React SPA — [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy; продукт в `/app/*` |
| `graphify-out/` | Локальный кэш Graphify (AST-графы), не документация |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| `AI_SKILLS.md` (удалён) | → `skills/*/SKILL.md` + [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) |
