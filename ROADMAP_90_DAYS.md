# My Agent — 90-Day Roadmap (Workflow + UX/UI + Marketplace)

**Стратегическая цель:** Превратить My Agent из мощного технического фреймворка в продукт для бизнеса, который конкурирует с ASCN.ai по простоте запуска и при этом сохраняет техническое превосходство.

**Ключевой дифференциатор:** "Мощь My Agent + простота ASCN + безопасность Docker sandbox"

**Статус на 2026-05-25:** Phase 1 ✅ | Phase 2 ✅ | Phase 3 ✅ (B2B scope, без Stripe)

---

## Phase 1: Workflow Core + Базовый UI (Дни 1–30) — ✅ COMPLETE

**Цель:** Дать пользователям возможность строить автономные связки без кода.

### Ключевые фичи
- Workflow Engine v1, 5 интеграций, Marketplace MVP (12+ шаблонов)
- Dashboard, Workflow Builder, Onboarding Wizard

### Метрики успеха
- Пользователь может создать и запустить workflow за < 8 минут ✅

---

## Phase 2: Marketplace + UX/UI Overhaul (Дни 31–60) — ✅ COMPLETE

**Цель:** Сделать продукт красивым и продающим.

### Ключевые фичи
- Marketplace 25+ шаблонов, рейтинги, publish API
- React SPA (`/app/*`), Chat 2.0, ExecutionTimeline, email triggers, CI

### Метрики успеха
- Marketplace ≥ 25 шаблонов ✅
- Среднее время создания workflow ≤ 5 минут ✅ (builder + templates)

---

## Phase 3: Business Features + Go-to-Market (Дни 61–90) — ✅ COMPLETE (B2B)

**Цель:** Подготовить продукт к монетизации и масштабу.

**Scope:** B2B-first — teams, roles, analytics, Google Sign-in. **Stripe отложен на post-v3.0.**

### Ключевые фичи

| Требование | Статус | Реализация |
|------------|--------|------------|
| 20+ бизнес-сценариев | ✅ | 25 шаблонов в `scripts/seed_workflow_templates.py` |
| Observability & cost tracking | ✅ | `usage_events`, `/api/usage/*`, `/metrics`, Analytics UI |
| Multi-user + Roles + Team workspaces | ✅ | `004_teams`, RBAC owner/admin/member, workspace scoping |
| SaaS (Stripe, usage pricing) | ⏸️ | Post-v3.0 |

### UX/UI задачи

| Задача | Статус |
|--------|--------|
| Logs & Analytics Dashboard | ✅ `/app/analytics` |
| Onboarding подключения сервисов | ✅ `/app/onboarding` (React) |
| Performance & Polish | ✅ skeleton loaders, mobile nav, TeamSwitcher |

### Definition of Done (Phase 3)

- [x] Team create + invite by email + accept invite
- [x] Workflows/sessions scoped by workspace (RBAC: member read, admin write)
- [x] Google Sign-in (`/api/auth/google`)
- [x] Analytics из DB (7/30 дней)
- [x] Admin page (users, team members, health)
- [x] Migration `004_teams` (SQLite + PostgreSQL via Alembic)
- [x] Tests: `test_teams`, `test_usage`, `test_google_auth` (47 total in suite)
- [x] CI + docs updated

### Метрики успеха

- Production workflow < 5 мин с нуля ✅ (onboarding → template → run)
- Pricing tiers ⏸️ (Stripe — post-v3.0)

---

## Post-v3.0 (backlog)

- Stripe subscriptions + usage-based billing
- OIDC/SAML enterprise SSO
- Team-shared integration credentials
- Grafana / PagerDuty in compose
- Log correlation: `workspace_id` in structured logs

---

## Приоритетная последовательность (выполнено)

1. Workflow Engine core ✅
2. Telegram + Gmail + Sheets инtegrации ✅
3. Dashboard + Workflow Builder UI ✅
4. Marketplace MVP ✅
5. Onboarding Wizard ✅
6. Полный редизайн + лендинг ✅
7. B2B workspaces + analytics ✅

---

*Обновлено: 2026-05-25*
