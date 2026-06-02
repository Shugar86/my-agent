# My Agent — Investor Demo Guide

> **TL;DR.** My Agent is an Autonomous Workflow OS that combines multi-agent
> AI research, a visual workflow builder, and a marketplace of templates.
> It replaces ~4 hours of analyst work in 90 seconds for the *Competitor
> Intelligence* killer use-case.
>
> Position: **n8n + Zapier + CrewAI in one product, with a marketplace.**
> Target: Knowledge workers in product, sales, ops and marketing.

---

## One-command launch (works without API keys)

```bash
cd /opt/projects/my-agent
docker compose --profile demo up -d --build
# Wait ~30s, then open:
# - http://localhost:8020/app   (My Agent)
# - http://localhost:5678        (n8n, basic auth: admin / demo)
```

Default login: `admin` / `admin` (set in `.env`, change before any external
showcase).

After login, templates and demo DOCX are seeded automatically on container
start (`scripts/entrypoint.sh`). Manual re-seed if needed:

```bash
docker compose exec agent python scripts/seed_workflow_templates.py
docker compose exec agent python scripts/generate_demo_artifact.py
```

The demo gracefully falls back to a prerecorded run if Kimi / OpenRouter /
Tavily keys are missing — the investor flow never breaks.

---

## Demo-MVP showcase (recommended for investor meetings)

**URL:** `http://localhost:8020/showcase#playground` — no login required (canonical entry).

Also: `http://localhost:8020/showcase` — full page with vertical cards + playground anchor.

| Section | What investor sees |
|---------|-------------------|
| Hero | 7 live / 23 personas / 50 templates |
| Vertical cards | 7 production cases with persona YAML accordion |
| Playground | Live Competitor Intelligence run (mock fallback) |
| Marketplace | 9 featured templates |
| CTA | Lead form → Telegram deep-link `@my_agent_demo_bot` |

**3-minute showcase script:**

| Time | Action |
|------|--------|
| 0:00 | Open **`/showcase#playground`** — hero + «Запустить demo» |
| 0:30 | Optional: scroll to vertical cards, expand 2–3 personas |
| 1:00 | Watch stepper (~30s mock replay) |
| 1:45 | Download DOCX brief |
| 2:00 | Scroll to marketplace preview or login → `/app/marketplace` |
| 2:30 | Optional: login → install template → builder |
| 3:00 | CTA form or wrap with metrics: $0.42, 18 420 tokens, ~4h saved |

Authenticated mirror: `/app/showcase` (same data from `website/data/showcase.json`).

**In-app demo (logged in):** `/app/demo` — same PlaygroundDemo as showcase, with competitor/beauty/lead presets and optional real run (needs API keys).

**Public template share:** `/app/share/templates/:id` — guest can preview; install redirects to `/login?next=...`.

---

## 3-minute investor script (in-app)

| Time  | Action | What the investor sees |
|-------|--------|------------------------|
| 0:00  | Open `http://localhost:8020/app` | Dashboard hero: "From a webhook to a competitive brief in 90 seconds." |
| 0:10  | Click **"Try 90s demo"** or open `/app/demo` | Modal or page: target = Notion, our_company = Linear |
| 0:15  | Click **Run demo** | Redirect to Workflow Builder. Nodes start lighting up one by one (pulsing green glow). |
| 0:30  | Inspector: 2 research agents run in parallel | Live SSE-style timeline with per-node durations: "r1 — 13.2s", "r2 — 12.5s" |
| 1:00  | Merge → analyst node activates | SWOT + 3 actions appear in the timeline detail |
| 1:25  | docs node generates DOCX | Real artifact ready to download (`competitor_brief_notion_vs_linear.docx`, 38 KB) |
| 1:35  | n8n hook triggered | (If n8n is up) execution `demo-exec-7421` starts in n8n |
| 1:50  | Click **"Open in builder"** / **"Marketplace"** | Show marketplace with featured template + thumbnail |
| 2:30  | Show **Onboarding** | Wizard step 1: live demo run → optional marketplace |
| 3:00  | Pitch wrap | Metrics card: $0.42 cost, 3h 58min saved, 18 420 tokens. |

---

## Key talking points

### The market
- Workflow automation: $19B+ TAM (n8n alone reached >50k stars on GitHub).
- AI agents: $5B in 2025, projected $200B+ by 2030 (Gartner).
- Knowledge workers: 1B+ globally; the average one has 4-6 SaaS tools and
  loses 20% of working hours to repetitive task chaining.

### The competition (and why we win)

| Competitor | What they do | Where we beat them |
|------------|--------------|--------------------|
| **n8n / Zapier / Make** | Visual automation, no AI-native | We embed multi-agent reasoning as first-class nodes — `agent.skill`, `deep_research`, `data_analyst` |
| **CrewAI / AutoGen** | Multi-agent frameworks for devs | We ship a UI + marketplace + onboarding non-developers can use |
| **OpenAI GPTs / Claude Skills** | Single-shot AI assistants | We orchestrate parallel agents into deterministic DAGs with retry, error edges, conditions |

### The wedge
The **marketplace + visual builder + multi-agent runtime** combination is
unique. Customers install a template (`tpl_competitor_intelligence`), tweak it
in the visual editor, and run it on a webhook trigger — all without writing
any code.

### Demo metrics (real numbers from the prerecorded run)

| Metric | Value |
|--------|-------|
| Total runtime | ~30 seconds |
| Human work replaced | ~4 hours |
| Tokens used | 18 420 |
| Cost (OpenRouter, GPT-4-class) | **$0.42** |
| Sources aggregated | 21 |
| Output artifact | DOCX, 4 sections, 38 KB |
| Cost-of-research compression | **~570x** |

---

## What's under the hood

- **Workflow engine** ([core/workflow/executor.py](core/workflow/executor.py)) —
  async DAG executor with retry policies, condition routing and persistent
  state (Postgres + Redis).
- **Multi-agent factory** ([core/auto_agent_factory.py](core/auto_agent_factory.py))
  — LLM analyses a task, spawns specialised sub-agents and synthesises results.
- **Node handlers** ([core/workflow/nodes/](core/workflow/nodes/)) —
  triggers, agents, conditions, util (merge / wait / code / set), actions
  (Telegram, Slack, Gmail, Sheets, Notion, HTTP, **n8n_webhook**).
- **React Flow UI** ([web/frontend/src/pages/WorkflowBuilder.tsx](web/frontend/src/pages/WorkflowBuilder.tsx))
  — drag-and-drop builder with live execution highlighting (pulsing nodes, edge
  flow animation).
- **Marketplace** ([web/frontend/src/pages/MarketplacePage.tsx](web/frontend/src/pages/MarketplacePage.tsx))
  — templates with ratings, install counts, featured section, share links.
- **Demo router** ([web/demo_router.py](web/demo_router.py)) — `POST /api/demo/run`
  (auth) and `POST /api/demo/public/run` (showcase, no auth) with mock fallback.
- **Leads router** ([web/leads_router.py](web/leads_router.py)) — `POST /api/leads/showcase`
  writes to `data/showcase_leads.jsonl`.
- **Showcase page** ([web/frontend/src/pages/PublicShowcasePage.tsx](web/frontend/src/pages/PublicShowcasePage.tsx))
  at `/showcase` — data from [website/data/showcase.json](website/data/showcase.json)
  via `/welcome-assets/data/showcase.json`.

---

## What we built in the last sprint (for credibility)

- New `action.n8n_webhook` node + `tpl_competitor_intelligence` template
  ([scripts/seed_workflow_templates.py](scripts/seed_workflow_templates.py)).
- Demo route with prerecorded fallback ([data/demo/competitor_run_sample.json](data/demo/competitor_run_sample.json)).
- Polished Dashboard hero, marketplace featured section, pulsing live nodes.
- Onboarding **starts** with a live demo run on step 1 (Competitor Intelligence).
- Optional n8n service in `docker-compose.yml` under `--profile demo`.

---

## Troubleshooting (during the demo)

- **No templates in marketplace** → run
  `docker compose exec agent python scripts/seed_workflow_templates.py`.
- **Demo button does nothing** → check the seed ran; the route returns 503 if
  `tpl_competitor_intelligence` is missing.
- **Real run fails** → uncheck "Real run" in the modal. Mock mode always works.
- **n8n hook fails** → expected without `--profile demo`; the demo continues
  successfully without it (the n8n node logs the missing URL and proceeds).
