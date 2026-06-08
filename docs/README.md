# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.2** · обновлено 2026-06-08.

**Primary LLM:** OpenRouter (`OPENROUTER_API_KEY`). Demo и showcase работают без ключей (mock fallback).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, быстрый старт Docker, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, навыки, troubleshooting |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, FeatureTag |

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, LLM, паттерны |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, Render/Railway/Fly |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки (включая PG sessions fix) |
| [HANDOFF.md](../HANDOFF.md) | Состояние продукта для новой сессии |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Запуск на Windows (CLI / Docker) |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 навыка) |
| [.env.example](../.env.example) | Переменные окружения (локальный Docker) |
| [deploy/.env.example](../deploy/.env.example) | Переменные для `deploy/docker-compose.prod.yml` |

---

## Исторические аудиты (архив)

Не обновляются при каждом релизе — снимок на дату аудита.

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Общий аудит 2026 |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX/metrics snapshot (3.5.0) |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Дорожная карта (завершённые фазы) |
| [.planning/](../.planning/) | Внутреннее планирование |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| `config/models.yaml` | Не загружается runtime; см. `config/agent.json` |
| `graphify-out/` | Сгенерированные артефакты анализа кода, не документация |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
