# My Agent — Investor Quick Reference

One-page cheat sheet for demos and pitch meetings.

## URLs

| Surface | URL | Notes |
|---------|-----|-------|
| **Canonical demo** | **`/showcase#playground`** | **Competitor Intelligence 90s → DOCX; no login; mock without API keys** |
| Demo-MVP showcase | `/showcase` | 7 vertical cases + playground |
| Landing | `/` | React landing; primary CTA → `/showcase#playground` |
| Public demo shortcut | `/demo` | Same playground (secondary entry) |
| Login | `/login` | Split SaaS layout; `?next=/app/onboarding` |
| Product | `/app` | Dashboard: demo modal + marketplace |
| Showcase (auth) | `/app/showcase` | Authenticated mirror |
| Dev creds | `/login?dev=1` | Shows `admin / admin` footer (internal only) |

## Env flags

| Variable | Purpose |
|----------|---------|
| `OPENROUTER_API_KEY` | Primary LLM (OpenRouter) for live chat & real demo runs (optional) |
| `TAVILY_API_KEY` | Real web search backend for live runs (optional) |
| `AGENT_PASSWORD` | Default admin password |

Demo works without LLM keys — public run uses prerecorded mock replay.

## 3-minute script

**Recommended:** open **`/showcase#playground`** → «Запустить demo» → wait ~30s → download DOCX → optional scroll vertical cards → CTA.

**After login:** `/app/marketplace` → install `tpl_competitor_intelligence` → `/app/workflows/:id`.

## Showcase verticals (7 cards)

Vertical cards use JSON-driven preview data (`mock` tag). Only playground is `live` backend.

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

## Demo-ready checklist

```bash
docker compose up -d --build
curl -sf http://localhost:8020/api/health
docker compose exec -T agent python -m pytest tests/test_demo_flow.py -q
# Browser: http://localhost:8020/showcase#playground
```

## Public API (showcase)

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/demo/public/run` | No |
| GET | `/api/demo/public/runs/{id}` | No |
| GET | `/api/demo/artifact/competitor_brief_notion_vs_linear.docx` | No |
| POST | `/api/leads/showcase` | No → `data/showcase_leads.jsonl` |

## E2E verification

```bash
cd web/frontend && npx playwright test e2e/investor-funnel.spec.ts
# Full canonical demo run (~90s):
E2E_DEMO_RUN=1 npx playwright test e2e/investor-funnel.spec.ts -g "Canonical demo"
```
