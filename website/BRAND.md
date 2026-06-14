# My Agent — Brand & Messaging

Единый narrative для investor funnel (React landing `/`, `/showcase`, `/demo`, login, `/app`).

## Positioning

**Tagline:** AI Agent OS — опишите задачу, получите работающего оператора

**One-liner:** AI-оператор для бизнеса за 2 минуты — без кода, без интегратора.

## Hero stats (social proof)

| Metric | Value |
|--------|-------|
| Шаблонов в marketplace | 50+ |
| Time-to-wow | ~10 сек (agent preview) |
| Готовых агентов | 10 |
| Live deployments | 7 vertical кейсов |

## Primary CTAs

1. **Live agent preview** — `/` hero widget или `/demo` (без login; mock без keys)
2. **7 vertical cases** — `/showcase` (investor meetings)
3. **Начать бесплатно** — `/login?next=/app/onboarding` → dashboard
4. **Chat** — `/app/chat` (после login)

## Glue narrative (везде в UI)

**Задача → Оператор → Результат** — пользователь описывает бизнес-задачу, платформа собирает persona + skills, оператор возвращает артефакт (документ, отчёт, ответ клиенту).

## Tone

- Professional, calm B2B
- Outcome-first (экономия часов, готовый оператор, артефакт на выходе)
- Без JWT, pip install, skills catalog на главной
- Честные статусы: Live / Beta / Preview / Скоро

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
| `website/style.css`, `marketing.css` | Legacy static (deprecated — assets only via `/welcome-assets`) |
| `website/login.css` | Login split layout |

Static HTML pages deprecated — see [`README-DEPRECATED.md`](README-DEPRECATED.md).

## Investor demo theme

Перед screen share рекомендуется **светлая тема** в `/app`: переключатель в sidebar или `localStorage.setItem('my-agent.theme', 'light')`.

Сценарий: [INVESTOR.md](../INVESTOR.md), [DEMO.md](../DEMO.md).
