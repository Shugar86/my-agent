# My Agent — Brand & Messaging

Единый narrative для investor funnel (React landing `/`, `/showcase`, `/demo`, login, `/app`).

## Positioning

**Tagline:** Autonomous Workflow OS — n8n + AI-агенты + marketplace

**One-liner:** Конкурентный brief за 90 секунд вместо 4 часов работы аналитика.

## Hero stats (social proof)

| Metric | Value |
|--------|-------|
| Шаблонов в marketplace | 50+ |
| Time-to-wow | 90 сек |
| Стоимость demo-run | $0.42 |
| Артефакт | DOCX brief |

## Primary CTAs

1. **Canonical demo** — `/showcase#playground` (mock без keys, no login)
2. **7 vertical cases** — `/showcase` (investor meetings)
3. **Landing CTA** — `/` → primary button → `/showcase#playground`
4. **Начать бесплатно** — `/login?next=/app/onboarding` → dashboard

## Glue narrative (везде в UI)

**Шаблон → Workflow → Результат** — полоска в PublicLayout и AppShell; блок в onboarding и landing `#product`.

## Tone

- Professional, calm B2B
- Outcome-first (часы сэкономлены, документ на выходе)
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
| `website/style.css`, `marketing.css` | Legacy static (deprecated — assets only via `/welcome-assets`) |
| `website/login.css` | Login split layout |

Static HTML pages deprecated — see [`README-DEPRECATED.md`](README-DEPRECATED.md).

## Investor demo theme

Перед screen share рекомендуется **светлая тема** в `/app`: переключатель в sidebar или `localStorage.setItem('my-agent.theme', 'light')`.
