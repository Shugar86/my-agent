# My Agent — Brand & Messaging

Единый narrative для investor funnel (React landing `/`, `/showcase`, `/demo`, login, `/app`).

## Positioning

**Tagline:** AI Agent OS для бизнеса — опишите задачу, получите оператора.

**One-liner:** AI-оператор для бизнеса за 2 минуты — без кода, без интегратора.

**Контекст:** n8n + CrewAI + marketplace в одном продукте, но для бизнес-пользователей, не разработчиков.

## Hero stats (social proof)

| Metric | Value |
|--------|-------|
| Шаблонов в marketplace | 50+ |
| Готовых агентов | 10 |
| Навыков (skills) | 33 |
| Live deployments | 7 vertical cases |

## Primary CTAs

1. **Live agent preview** — `/` hero widget или `/demo` (без login)
2. **7 vertical cases** — `/showcase` (investor meetings)
3. **Начать бесплатно** — `/login?next=/app/onboarding` → dashboard
4. **Чат с агентом** — `/app/chat` (после login)

## Glue narrative (везде в UI)

**Задача → Оператор → Результат** — пользователь описывает задачу, платформа собирает persona + skills + workflow.

## Tone

- Professional, calm B2B
- Outcome-first (экономия часов, готовый документ, работающий оператор)
- Честные статусы (Live / Beta / Preview / Скоро)
- Без JWT, pip install, skills catalog на главной

## Visual bridge

- **Marketing (React):** light cream `#FDFCF8`, accent `#FF4D00`, Manrope + Inter — [`web/frontend/src/layout/landing.css`](../web/frontend/src/layout/landing.css)
- **Product:** GitHub-dark в `/app`; device frame на лендинге — тёмный скрин dashboard

## Status badges (FeatureTag)

| Status | Meaning |
|--------|---------|
| Live | Backend connected |
| Beta | Works, may be unstable |
| Preview | Mock / static data |
| Скоро | UI only (e.g. Stripe billing) |

Registry: `web/frontend/src/config/featureRegistry.ts`

## CSS / assets

| File | Scope |
|------|-------|
| `web/frontend/src/layout/landing.css` | React landing sections |
| `web/frontend/src/layout/theme.css` | Product SPA (dark/light) |
| `website/style.css`, `marketing.css` | Legacy static (deprecated — см. [README-DEPRECATED.md](./README-DEPRECATED.md)) |

## Связанные документы

- [DEMO.md](../DEMO.md) — сценарий live demo
- [INVESTOR.md](../INVESTOR.md) — 3-минутный питч
- [AGENTS.md](../AGENTS.md) — вайб и контракт продукта
