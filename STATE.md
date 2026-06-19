# STATE — my-agent

*Updated: 2026-06-19*

## Status

**Active** — продукт v4.0.0 (Agent OS pivot): живой лендинг, public agent preview, OpenRouter как primary LLM. Документация синхронизирована с v4 (2026-06-19).

## What is happening now

| Поле | Значение |
|------|----------|
| Ветка | `main` |
| Версия (README / docs) | 4.0.0 |
| Primary LLM | OpenRouter (`OPENROUTER_API_KEY`) |
| Фокус | Trust & Polish (ROADMAP Phase 1) |
| pyproject.toml version | 2.0.0 (package version, не product version) |

## Blockers

| Блокер | Влияние |
|--------|---------|
| ROADMAP Phase 1 не закрыт | Frontend build + VDS deploy, smoke/E2E agent-preview — не подтверждены в prod |
| OPEN backlog в [TROUBLES.md](TROUBLES.md) | H13 wizard plaintext keys; H9 docker sandbox in container; M2 chunked bypass; M6-pg destructive DROP |
| Alembic PG на prod | В gate не прогонялся локально без PG — [uncertain] для prod migrations |

Критических открытых CRITICAL/HIGH после re-audit 2026-05-27 нет (gate 60/60 PASS).

## Last release / milestone

**v4.0.0** (2026-05-28):

- Pivot narrative: «AI-оператор для бизнеса за 2 минуты»
- Landing redesign: AgentPreviewWidget, showcase cards, chat-first dashboard
- Endpoints: `POST /api/demo/public/agent-preview`, `agent-chat`
- Kimi → OpenRouter; SSE chat persistence в PG
- Deploy: `AGENT_PASSWORD` ≥12, `.env.example` обновлён

## Docs health (2026-06-19)

Синхронизированы: `docs/README.md`, `PROJECT_GUIDE.md`, `ARCHITECTURE.md`, `DEPLOYMENT.md`, `SERVER.md`, `website/BRAND.md`.

Удалены мёртвые ссылки на `AUDIT_*.md`, `HANDOFF.md`. Добавлен `website/README-DEPRECATED.md`.
