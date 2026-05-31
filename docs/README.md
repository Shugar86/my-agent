# Документация My Agent

> Индекс актуальной документации. Версия продукта: **3.5.3** (2026-05-31).

---

## С чего начать

| Документ | Для кого | Содержание |
|----------|----------|------------|
| [README.md](../README.md) | Все | Обзор, Docker quick start, маршруты UI |
| [PROJECT_GUIDE.md](../PROJECT_GUIDE.md) | RU | Установка, CLI, skills, troubleshooting |
| [DEMO.md](../DEMO.md) | Демо / инвесторы | Сценарий 90 сек, Competitor Intelligence |
| [INVESTOR.md](../INVESTOR.md) | Питч | URL, env, 3-минутный скрипт |
| [website/BRAND.md](../website/BRAND.md) | Маркетинг | Positioning, CTAs, tone |

**Канонический demo URL:** `http://localhost:8020/showcase#playground` (без логина, mock без API keys).

---

## Разработка и эксплуатация

| Документ | Содержание |
|----------|------------|
| [ARCHITECTURE.md](../ARCHITECTURE.md) | Слои, workflow engine, LLM gateway |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Локальный и production деплой |
| [SERVER.md](../SERVER.md) | VDS, порты, nginx, бэкапы |
| [deploy/README.md](../deploy/README.md) | Docker prod, Render/Railway/Fly, мониторинг |
| [SECURITY.md](../SECURITY.md) | JWT, rate limits, production checklist |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Типичные ошибки (вкл. Postgres sessions 3.5.2) |
| [HANDOFF.md](../HANDOFF.md) | Состояние продукта для новой сессии / automation |
| [WINDOWS_LAUNCH.md](../WINDOWS_LAUNCH.md) | CLI на Windows |
| [web/frontend/DESIGN.md](../web/frontend/DESIGN.md) | UI design system (React) |
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | CI: pytest + frontend build |

---

## Справочники

| Документ | Содержание |
|----------|------------|
| [CHANGELOG.md](../CHANGELOG.md) | История релизов |
| [skills/*/SKILL.md](../skills/) | 33 skills — документация каждого навыка |
| [agents/registry.json](../agents/registry.json) | 7 профилей агентов |
| [.env.example](../.env.example) | Переменные окружения |

---

## LLM и ключи (актуально с 3.5.2)

| Приоритет | Переменная | Назначение |
|-----------|------------|------------|
| **Primary** | `OPENROUTER_API_KEY` | `openrouter/owl-alpha` в `config/agent.json` |
| Fallback | тот же ключ | `google/gemini-2.5-flash-preview` через OpenRouter |
| Опционально | `KIMI_API_KEY` | Kimi Code API (legacy / альтернатива) |
| Demo search | `TAVILY_API_KEY` | Живой веб-поиск в demo-run |

Без ключей: публичный showcase и investor demo используют **mock replay** — поток не ломается.

---

## Исторические материалы (архив)

Не обновляются при каждом релизе — снимок на дату.

| Файл | Тема |
|------|------|
| [AUDIT_PRODUCTION_2026.md](../AUDIT_PRODUCTION_2026.md) | Production readiness (3.4) |
| [AUDIT_PRODUCT_2026.md](../AUDIT_PRODUCT_2026.md) | Product depth |
| [AUDIT_2026.md](../AUDIT_2026.md) | Общий аудит 2026 |
| [AUDIT_REPORT.md](../AUDIT_REPORT.md) | UX/metrics snapshot |
| [ROADMAP_90_DAYS.md](../ROADMAP_90_DAYS.md) | Дорожная карта (завершённые фазы) |
| [.planning/](../.planning/) | Внутреннее планирование |

---

## Не использовать / не документация

| Путь | Причина |
|------|---------|
| `website/*.html` | Legacy static — UI в React SPA, см. [website/README-DEPRECATED.md](../website/README-DEPRECATED.md) |
| `web/static/*.html` (кроме login) | Legacy; продукт в `/app/*` |
| `graphify-out/` | Сгенерированные артефакты анализа кода, не часть продукта |
| Порт **8000** в старых заметках | Актуальный порт Docker/VDS: **8020** |
| Удалённые файлы | `CONTEXT.md`, `SESSION_HISTORY.md`, `AI_SKILLS.md` — заменены этим индексом и `skills/*/SKILL.md` |
