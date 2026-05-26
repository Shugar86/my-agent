# My Agent — Audit Report

> **Date:** 2026-05-26  
> **Version:** 3.5.0  
> **Scope:** UX audit — React landing migration, demo IA, status badges, onboarding explainer

---

## Executive Summary

My Agent is an **Autonomous Workflow OS**: unified React SPA (public `/` + product `/app`), FastAPI backend, 52 marketplace templates, Kimi K2.6 primary LLM, visual DAG builder (21 node types), investor demo with mock fallback.

**Product maturity:** Strong as **investor/demo + B2B onboarding platform**. v3.5.0 unifies marketing and product in one React bundle; public demo works without auth via `/api/demo/public/run`.

---

## Metrics (verified 2026-05-26)

| Metric | Value |
|--------|------:|
| Version | 3.5.0 |
| Marketplace templates | 52 (3 draft, 3 featured demo) |
| Workflow node types | 21 |
| Registered agents | 10 |
| Universal agent tools | 61 (ghost tools removed) |
| Skills with SKILL.md | 33 |
| pytest modules | 47+ |
| API route handlers | ~130 |
| Frontend SPA pages | 17 (+ LandingPage, PublicDemoPage, PublicShowcasePage) |
| Integrations (registry) | 6 (google, telegram, slack, notion, n8n, webhook) |

---

## What Works

- React landing at `/` with embedded live demo (PlaygroundDemo publicMode)
- Public `/demo`, `/showcase` without auth (same SPA bundle)
- Kimi Code API chat + workflow agents
- Docker entrypoint auto-seed + demo DOCX
- Honest workflow run status (failed actions → failed run)
- Marketplace browse/install + template demo-run (mock)
- JWT auth + workspace teams + run access checks
- Onboarding explainer + offline demo fallback
- FeatureTag system (Live / Beta / Preview / Скоро) on nav, tabs, demos
- `useDemoAwareFetch` for showcase data with preview toast

---

## Resolved in v3.5.0 (UX audit)

| Issue | Fix |
|-------|-----|
| Split static HTML vs React SPA (confusing IA) | `/`, `/demo`, `/showcase` → React; `website/*.html` deprecated |
| `/app/demo` orphan (not in sidebar) | Nav item «Live demo 90s» |
| Misleading ararat «Открыть виджет» CTA | «Установить шаблон» in showcase.json |
| Onboarding skips product understanding | Explainer + ProductNarrative before demo step |
| Mock demo failures silent | Unified preview banner in PlaygroundDemo |
| Marketplace install without loading | `installingId` / `previewLoadingId` states |
| WorkflowList silent API errors | Error banner + retry |
| Settings agents/knowledge/mcp buried | Sidebar quick links + tab badges |
| PublicTemplatePage always Preview | `beta` when live API data loaded |

## Resolved in v3.4.3 (UX funnel)

| Issue | Fix |
|-------|-----|
| Onboarding step 2 empty without showcase JSON | `fetchWithDemoFallback` + `ONBOARDING_USECASE_FALLBACK` |
| DemoModal closes on failed run | Close only on success; retry UI |
| Dashboard/landing hero duplication | Split copy: landing = outcome pitch; dashboard = first workflow |
| CTA overload on dashboard | 2 CTAs: marketplace + demo modal |
| Offline demo instant (not cinematic) | Timed step replay in `PlaygroundDemo` |
| Analytics silent API failure | Explicit error banner |
| Chat beta without API key guidance | Empty state + toolbar hint → Settings → Models |

## Resolved in v3.4.2 (UX audit)

- Public template share blocked by auth middleware → `/app/share` in `PUBLIC_PREFIXES`
- Misleading Live badges on static showcase cards → `FeatureTag` story/preview
- `fetchWithDemoFallback` noop → bundled JSON fallback
- Showcase orphan route → sidebar «Кейсы»; install-similar CTAs per vertical

## Known Gaps (next iteration)

| Gap | Severity | Notes |
|-----|----------|-------|
| Stripe billing | Medium | Plan limits in DB; no payment provider |
| WorkflowBuilder monolith refactor | Low | ~900 lines; split hooks |
| E2E templates without credentials | Medium | Demo-run mock covers preview |
| `trigger.email` / `trigger.new_lead` | Low | Hidden from builder palette |
| HubSpot/Airtable connectors | Low | Not in registry yet |
| WorkflowList schedule shows raw job.id | Low | P2 backlog |

---

## Test Commands

```bash
docker compose up -d --build agent
docker compose exec -T agent python -m pytest tests/test_marketplace.py tests/test_kimi_provider.py tests/test_workspace_isolation.py -q
cd web/frontend && bun run build
cd web/frontend && bun run test:e2e   # server on :8020
```

---

## Deploy

```bash
git push origin main   # or vds remote
vds-push && vds-deploy my-agent
```

Optional monitoring stack:

```bash
docker compose --profile monitoring up -d prometheus grafana
# Grafana: http://127.0.0.1:3001 (admin/admin)
```
