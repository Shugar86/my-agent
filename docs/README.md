# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.3** (2026-06-09).

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
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои системы, workflow engine, паттерны |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker Compose prod, Render/Railway/Fly, systemd |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки |
| [HANDOFF.md](../HANDOFF.md) | Состояние продукта для новой сессии |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | Запуск CLI на Windows |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | Документация каждого skill (33 навыка) |
| [.env.example](../.env.example) | Переменные окружения |
| `config/agent.json` | Primary LLM (`openrouter/owl-alpha`) |
| `core/configurator.py` | Профили моделей (`fast`, `balanced`, `smart`, `kimi`, `local`) |

---

## Исторические материалы (архив)

Не обновляются при каждом релизе — снимок на дату аудита или milestone.

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Общий аудит 2026 |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX/metrics snapshot (3.5.0) |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Дорожная карта 90 дней (завершена) |
| [.planning/](../.planning/) | Внутреннее планирование |

---

## Устаревшее (не использовать)

| Путь | Причина |
|------|---------|
| `website/*.html` | Статический лендинг заменён React SPA — см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `config/models.yaml` | DEPRECATED — профили в `core/configurator.py` |
| `AI_SKILLS.md` (удалён) | Сводка перенесена в `skills/*/SKILL.md` и [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) |
| `web/static/*.html` (кроме login) | Legacy HTML; продукт в `/app/*` |
| `graphify-out/` | Сгенерированные артефакты code-graph; не документация |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
