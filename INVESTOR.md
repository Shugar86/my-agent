# My Agent — Investor Quick Reference

One-page cheat sheet for demos and pitch meetings.

## URLs

| Surface | URL | Notes |
|---------|-----|-------|
| Landing | `/` or `/welcome` | Outcome pitch; **primary CTA → `/demo`** |
| **Demo-MVP showcase** | **`/showcase`** (public) or **`/app/showcase`** (auth) | **7 vertical cases + `#playground` demo** |
| Public demo | `/demo` | Competitor Intelligence only; no login |
| Login | `/login` | Split SaaS layout; `?next=/app/onboarding` |
| Product | `/app` | Dashboard: «Выбрать шаблон» + demo modal; GettingStartedBanner if no workflows |
| Showcase (auth) | `/app/showcase` | Sidebar «Кейсы и demo»; PlaygroundDemo + install similar |
| Dev creds | `/login?dev=1` | Shows `admin / admin` footer (internal only) |

## Env flags

| Variable | Purpose |
|----------|---------|
| `DEMO_USER_ID` | Fixed user for public demo runs (optional) |
| `AGENT_PASSWORD` | Default admin password |
| `OPENROUTER_API_KEY` | Enables real demo mode (optional) |

## 3-minute script

**Recommended (Demo-MVP):** `/showcase` → scroll 7 vertical cards → playground «Запустить demo» → CTA form.

**Classic funnel:** `/` (CTA → `/demo`) → login → `/app/onboarding` → dashboard.

**In-app first-run:** `/app` → GettingStartedBanner → marketplace install OR demo modal.

## Showcase verticals (7 cards)

| # | Vertical | Status | Proof |
|---|----------|--------|-------|
| 1 | Mary Jewelry (ai-tutor) | Production | Telegram bot, persona YAML |
| 2 | PEGAS Touristik channel | Production | @pegasszm, 2 posts/day |
| 3 | Podolog VK channel | Production | VK longreads |
| 4 | DocBrain | Production | docbrain.online, Stripe $4.99 |
| 5 | Pretenzia | Production | pretenziaonline.ru, Robokassa 190 ₽ |
| 6 | Sales-bot kormoved | R&D Lab | Anti-detect, good/bad training |
| 7 | My Agent workflow OS | Demo stack | 90s / $0.42 / DOCX brief |

Data source: [website/data/showcase.json](website/data/showcase.json)

## Key metrics (mock run)

- **90 sec** time-to-wow
- **$0.42** per run
- **18 420** tokens
- **~4 hours** analyst work replaced
- **50+** marketplace templates

## Brand copy

Source: [website/BRAND.md](website/BRAND.md)

- Tagline: *Autonomous Workflow OS — n8n + AI-агенты + marketplace*
- Hero: *Конкурентный brief за 90 секунд вместо 4 часов*

## Investor demo theme

Before screen share, switch `/app` to **light theme** (sidebar toggle) or run:

```js
localStorage.setItem('my-agent.theme', 'light');
location.reload();
```

## Pre-demo checklist

1. `python scripts/seed_workflow_templates.py`
2. `python scripts/generate_demo_artifact.py`
3. Server on `:8020`
4. Optional: record `website/assets/demo.mp4` for landing video block

## Public API (showcase)

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/demo/public/run` | No |
| GET | `/api/demo/public/runs/{id}` | No |
| POST | `/api/leads/showcase` | No → `data/showcase_leads.jsonl` |

## E2E verification

```bash
cd web/frontend && npx playwright test e2e/investor-funnel.spec.ts
# Full demo run (90s) on /demo or /showcase playground:
E2E_DEMO_RUN=1 npx playwright test e2e/investor-funnel.spec.ts -g "mock run"
E2E_DEMO_RUN=1 npx playwright test e2e/investor-funnel.spec.ts -g "Showcase"
```
