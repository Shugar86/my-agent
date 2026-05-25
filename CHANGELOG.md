# Changelog — My Agent

## 3.3.0 — 2026-05-26 (Architectural fix, iterations 1–2)

### Backend
- Kimi Code API as primary LLM (`core/kimi_provider.py`, `resolve_agent_model_config`)
- Docker entrypoint auto-seeds templates + generates demo DOCX on startup
- Workflow executor: failed actions no longer report run as `success`
- `agent.skill` node respects `"skill"` config key (singular)
- `action.webhook` supports GET; `action.n8n_webhook` added to NodeType enum
- Ghost tools removed from universal agent registry; SKILL.md for web3/voice_io/video_processing
- Seed upsert for draft templates; `tpl_lead_qualify` uses `trigger.webhook`
- Draft templates excluded from marketplace popular sort

### Frontend (RU)
- WorkflowBuilder full i18n (~40 keys)
- Marketplace admin Publish modal RU
- Dashboard integrations stat uses `configured`
- PublicTemplate install: toast on error, login redirect only on 401
- Onboarding friendly fallback when template install returns 404
- Removed orphan `AgentBuilderPage.tsx`

### Demo / ops
- 3 demo presets (competitor, beauty, lead) + sample JSON/DOCX artifacts
- A2A queue in Redis; WebSocket JWT auth
- Tests: `test_kimi_provider.py`, marketplace suite (25 passed in container)

---

## 3.2.0 — 2026-05-26 (UI/UX polish)

- React SPA on `/app/*` with RU i18n and PWA
- Demo-MVP showcase at `/showcase`
- Onboarding wizard, Dashboard hero, marketplace browse

---

## 3.1.0 and earlier

See git history and `SESSION_HISTORY.md`.
