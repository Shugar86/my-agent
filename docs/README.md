# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.3** (2026-06-05).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, Docker quick start, маршруты UI, env |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, skills, API, troubleshooting |
| [HANDOFF.md](../HANDOFF.md) | Новая сессия / агент | Текущее состояние, demo checklist, ключевые файлы |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Windows | CLI/TUI без Docker |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои, workflow engine, LLM gateway, data stores |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, systemd, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker prod, Render/Fly/Railway, мониторинг |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки (в т.ч. Postgres sessions 3.5.2) |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | CI: pytest + frontend build |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | 33 доменных skill (SKILL.md + skill.py) |
| [.env.example](../.env.example) | Переменные окружения (корень репозитория) |
| [deploy/.env.example](../deploy/.env.example) | Env для `deploy/docker-compose.prod.yml` |
| [config/models.yaml](../config/models.yaml) | Профили CLI: fast, balanced, smart |
| [agents/registry.json](../agents/registry.json) | 7 профилей агентов |

---

## Стек (кратко)

| Компонент | Значение |
|-----------|----------|
| Версия | 3.5.3 |
| Web / Docker | порт **8020** (не 8000) |
| Primary LLM | **OpenRouter** (`OPENROUTER_API_KEY`, `openrouter/owl-alpha` в `config/agent.json`) |
| Опционально | Kimi Code API (`KIMI_API_KEY`), Tavily (`TAVILY_API_KEY`) |
| БД / очередь (prod) | PostgreSQL + Redis (обязательны при `ENV=production`) |
| UI | React 18 SPA (`web/frontend/` → `web/static/app/`) |
| Marketplace | 52 шаблона (`scripts/seed_workflow_templates.py`) |

Демо без API-ключей: mock replay на `/showcase#playground` и `/api/demo/public/run`.

---

## Исторические материалы (архив)

Не обновляются при каждом релизе — снимок на дату аудита или спринта.

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Общий аудит (устаревший LLM-стек: Kimi) |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX/metrics snapshot (3.5.0) |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Дорожная карта May 2026 (завершённые фазы) |
| [.planning/](../.planning/) | Внутреннее планирование |

---

## Не использовать / не документировать как продукт

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| `graphify-out/` | Сгенерированные артефакты Graphify, не часть рантайма |
| Порт **8000** в старых заметках | Актуальный порт: **8020** |
| `AI_SKILLS.md` (удалён) | Заменён на `skills/*/SKILL.md` и [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) |
