# My Agent — Audit Report

> **Date:** 2026-05-26  
> **Version:** 3.4.3  
> **Scope:** UX funnel iteration — onboarding, dashboard IA, demo polish

---

## Executive Summary

My Agent is an **Autonomous Workflow OS**: React SPA (`/app`), FastAPI backend, 52 marketplace templates, Kimi K2.6 primary LLM, visual DAG builder (21 node types), investor demo with mock fallback.

**Product maturity:** Strong as **investor/demo platform**. v3.4.3 closes first-run funnel gaps: onboarding never renders empty, dashboard/landing narratives split, demo modal retry.

---

## Metrics (verified 2026-05-26)

| Metric | Value |
|--------|------:|
| Version | 3.4.3 |
| Marketplace templates | 52 (3 draft, 3 featured demo) |
| Workflow node types | 21 |
| Registered agents | 10 |
| Universal agent tools | 61 (ghost tools removed) |
| Skills with SKILL.md | 33 |
| pytest modules | 47+ |
| API route handlers | ~130 |
| Frontend SPA pages | 14 |
| Integrations (registry) | 6 (google, telegram, slack, notion, n8n, webhook) |

---

## What Works

- Kimi Code API chat + workflow agents
- Docker entrypoint auto-seed + demo DOCX
- Honest workflow run status (failed actions → failed run)
- Background workflow execution (non-blocking HTTP)
- Marketplace browse/install + template demo-run (mock)
- JWT auth + workspace teams + run access checks
- Prometheus `/metrics` + optional Grafana profile
- RU i18n for builder, marketplace, settings
- Onboarding use-case step with offline fallback cards
- Offline demo animated step replay (no API required)
- Dashboard GettingStartedBanner for empty workspaces

---

## Resolved in v3.4.3 (UX funnel)

| Issue | Fix |
|-------|-----|
| Onboarding step 2 empty without showcase JSON | `fetchWithDemoFallback` + `ONBOARDING_USECASE_FALLBACK` |
| DemoModal closes on failed run | Close only on success; retry UI |
| Dashboard/landing hero duplication | Split copy: landing = outcome pitch; dashboard = first workflow |
| CTA overload on dashboard | 2 CTAs: marketplace + demo modal |
| External `/showcase` link in sidebar confuses IA | Removed from sidebar; small link on dashboard cases |
| Offline demo instant (not cinematic) | Timed step replay in `PlaygroundDemo` |
| `getDemoSample()` unused | Wired into demo completion metrics |
| Analytics silent API failure | Explicit error banner |
| Chat beta without API key guidance | Empty state + toolbar hint → Settings → Models |

## Resolved in v3.4.2 (UX audit)

- Public template share blocked by auth middleware → `/app/share` in `PUBLIC_PREFIXES`
- Misleading Live badges on static showcase cards → `FeatureTag` story/preview
- `fetchWithDemoFallback` noop (same URL twice) → bundled JSON fallback
- Showcase orphan route → sidebar «Кейсы»; install-similar CTAs per vertical

## Known Gaps (next iteration)

| Gap | Severity | Notes |
|-----|----------|-------|
| E2E templates without credentials | Medium | Demo-run mock covers preview; real delivery needs integrations |
| `trigger.email` / `trigger.new_lead` | Low | Hidden from builder palette |
| Stripe billing | Medium | Plan limits in DB; no payment provider |
| HubSpot/Airtable connectors | Low | Not in registry yet |
| PublicTemplatePage copy link / 404 UX | Low | P2 backlog |
| WorkflowList schedule shows raw job.id | Low | P2 backlog |

---

## Test Commands

```bash
docker compose up -d --build agent
docker compose exec -T agent python -m pytest tests/test_marketplace.py tests/test_kimi_provider.py tests/test_workspace_isolation.py -q
cd web/frontend && bun run build
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
