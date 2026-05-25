# My Agent — Project Vision

## Overview

My Agent is a modular AI agent platform evolving into a **business automation product** — workflow engine + marketplace + AI agents. Competes with ASCN.ai on simplicity while retaining technical depth (MCP, A2A, Docker sandbox).

## Core Value Proposition (2026-05-25)

1. **Workflow Automation** — n8n-like drag-and-drop builder with AI agent nodes
2. **Marketplace** — 10+ ready-to-run business workflow templates
3. **5 Key Integrations** — Telegram, Gmail, Google Sheets, Slack, Notion
4. **Universal Assistant** — AI auto-selects skills for complex tasks
5. **Production-Ready** — SQLite/PostgreSQL, JWT auth, Docker sandbox, 400+ tests

## Target Users

- Small business owners automating sales, support, marketing
- Solo founders needing no-code + AI power
- Teams wanting self-hosted alternative to Zapier/n8n + ChatGPT

## Technology Stack

- **Backend:** Python 3.11+, FastAPI, LiteLLM, Workflow Engine (JSON DAG)
- **Frontend:** Vanilla HTML (dashboard) + React Flow SPA (workflow builder)
- **Persistence:** SQLite (dev) / PostgreSQL (prod), Alembic migrations
- **Integrations:** Google APIs, Notion, Telegram, Slack

## Current Status (Phase 1)

See `ROADMAP_90_DAYS.md` and `.planning/STATE.md`.

## Next Milestone

Phase 2 (days 31–60): Marketplace overhaul, Agent Builder 2.0, full UI redesign.
