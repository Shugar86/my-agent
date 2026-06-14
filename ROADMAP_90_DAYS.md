# My Agent — Roadmap

**Стратегия:** AI Agent OS — no-code создание AI-операторов для бизнеса.
Позиция между n8n/Zapier (сложно) и AI-студиями (дорого).

**Статус:** v4.0.0 — landing redesign, agent preview, chat reliability.

---

## Done (v4.0.0)

- Landing: hero с live AgentPreviewWidget, showcase cards, chat-first dashboard
- Agent Preview: `POST /api/demo/public/agent-preview` + `/agent-chat` (live LLM)
- Kimi → OpenRouter migration complete
- SSE chat persistence fix
- Unified PG/SQLite session storage
- Deploy: password validation, env examples
- Rate limiting + prompt injection protection
- 7 live deployments (Mary Jewelry, PEGAS, DocBrain, Pretenzia и др.)
- Документация синхронизирована с v4 (2026-06-14)

## Next — Phase 1: Trust & Polish

- [ ] Frontend build + VDS deploy
- [ ] Smoke test: agent-preview endpoint live
- [ ] E2E test: landing → agent preview → showcase cards
- [ ] ChatPage: reload thread → messages visible (verify PG path)

## Phase 2: Agent Builder UX

- [ ] Guided agent creation wizard (не CRUD text fields)
- [ ] Skills picker (checkbox grid, не comma-separated text)
- [ ] Inline test chat на карточке агента
- [ ] Save agent from preview widget (post-login flow)

## Phase 3: Channel Connect

- [ ] Telegram bot setup wizard (token → test → deploy)
- [ ] Webhook channel connect UI
- [ ] Agent → channel mapping в settings

## Phase 4: VibeCraft Integration

- [ ] Persona YAML в my-agent (role → vibe.role + vibe.voice + behavior)
- [ ] ResponseComposer из ai-tutor-engine
- [ ] Agent evolution (VibeMorph — feedback → persona tuning)

## Not planned (backlog)

- Docker sandbox в контейнере (docker.sock mount)
- Competitor Intelligence DOCX from live run
- Pricing page на лендинге
- Billing / Stripe integration
