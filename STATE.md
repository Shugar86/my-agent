# STATE — my-agent

*Updated: 2026-06-15*

## Status

**Active** — продукт в фазе v4.0.0 (Agent OS pivot): живой лендинг, public agent preview, OpenRouter как primary LLM, закрытые CRITICAL/HIGH из аудитов TROUBLES.

## What is happening now

| Поле | Значение |
|------|----------|
| Ветка | `main` |
| Версия | 4.0.0 |
| Фокус | Док-синхронизация v4; Phase 1 Trust & Polish (VDS deploy, E2E agent-preview) |
| Документация | Синхронизирована с v4 narrative (ARCHITECTURE, PROJECT_GUIDE, BRAND, docs index) |

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

## Planned (следующие шаги)

1. **Phase 1 Trust & Polish** — собрать frontend, задеплоить на VDS, smoke `agent-preview` live.
2. **E2E** — landing → agent preview → showcase cards; проверить ChatPage reload с PG.
3. **Phase 2 Agent Builder UX** — wizard, skills picker, inline test chat, save from preview post-login.
4. **Backlog PR** — закрыть выбранные OPEN из TROUBLES (H13, H9) отдельными PR.

См. полный план: [ROADMAP_90_DAYS.md](ROADMAP_90_DAYS.md).
