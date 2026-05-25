# My Agent — Brand & Messaging

Единый narrative для investor funnel (landing, `/showcase`, `/demo`, login, `/app`).

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

1. **7 vertical cases** — `/showcase` (primary для инвесторской встречи)
2. **Live playground** — `/showcase#playground` (Competitor Intelligence, без auth)
3. **Смотреть демо 90 сек** — `/demo` (узкий сценарий)
4. **Начать бесплатно** — `/app/onboarding` или `/login`

## Tone

- Professional, calm B2B
- Outcome-first (часы сэкономлены, документ на выходе)
- Без JWT, pip install, skills catalog на главной

## Visual bridge

- **Marketing:** light cream `#FDFCF8`, accent `#FF4D00`, Manrope + Inter
- **Product:** GitHub-dark в `/app`; скриншоты на лендинге — в тёмных device frames

## Motion & elevation

| Token | Value | Use |
|-------|-------|-----|
| `--motion-fast` | 200ms | Hover, focus |
| `--motion-base` | 350ms | Nav, cards |
| Card hover | `translateY(-2px)` + `--shadow-hover` | Steps, pricing, use cases |
| Scroll reveal | `.reveal` → `.visible` | Sections on landing |

**Reduced motion:** при `prefers-reduced-motion: reduce` scroll reveal отключается (`main.js`).

## Spacing

- Section padding desktop: **120px** (`--section-pad`)
- Section padding mobile: **80px**

## CSS files

| File | Scope |
|------|-------|
| `style.css` | Tokens, nav, buttons, device frame, reveal |
| `marketing.css` | Landing sections, demo page |
| `showcase.css` | Demo-MVP showcase page |
| `login.css` | Login split layout |

## Investor demo theme

Перед screen share рекомендуется **светлая тема** в `/app`: переключатель в sidebar или `localStorage.setItem('my-agent.theme', 'light')`.
