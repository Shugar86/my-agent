# STATE — my-agent

*Updated: 2026-05-30*

## Status

**Active** — продукт в фазе v4.0.0 (Agent OS pivot): живой лендинг, public agent preview, миграция LLM на OpenRouter, закрытые CRITICAL/HIGH из аудитов TROUBLES. Репозиторий синхронизирован с `vds/main`, незакоммиченных изменений нет.

## What is happening now

| Поле | Значение |
|------|----------|
| Ветка | `main` (tracking `vds/main`) |
| Версия (README) | 4.0.0 |
| Фокус коммитов | Порт 8020 наружу; LLM fallback по free-моделям при 429; non-fatal entrypoint seed; удаление Kimi provider; routing OpenRouter для demo |
| Последние коммиты | `44ade1f` LLM fallback + port; `6bf36cd` entrypoint; `5c985a2` Kimi kill; `ea443a6` v4 pivot (landing, chat PG) |
| Uncommitted | Нет |

Документация частично отстаёт от v4: `ARCHITECTURE.md` (3.5.0, упоминание Kimi), `docs/README.md` (3.5.0), `PROJECT_GUIDE.md` (Kimi primary), `website/BRAND.md` (старый narrative «90 сек brief»).

## Blockers

| Блокер | Влияние |
|--------|---------|
| ROADMAP Phase 1 не закрыт | Frontend build + VDS deploy, smoke/E2E agent-preview и chat reload — не подтверждены в prod |
| OPEN backlog в [TROUBLES.md](TROUBLES.md) | H13 wizard plaintext keys; H9 docker sandbox in container; M2 chunked bypass; M6-pg destructive DROP; infra Caddy/n8n |
| Расхождение версий docs | Риск путаницы при onboarding (pyproject 2.0.0 vs README 4.0.0) |
| Alembic PG на prod | В gate не прогонялся локально без PG — [uncertain] для prod migrations |

Критических открытых CRITICAL/HIGH после re-audit 2026-05-27 нет (gate 60/60 PASS).

## Last release / milestone

**v4.0.0** (2026-05-28, коммит `ea443a6` и последующие fix):

- Pivot narrative: «AI-оператор для бизнеса за 2 минуты»
- Landing redesign: AgentPreviewWidget, showcase cards, chat-first dashboard
- Endpoints: `POST /api/demo/public/agent-preview`, `agent-chat`
- Kimi → OpenRouter; SSE chat persistence в PG
- Deploy: `AGENT_PASSWORD` ≥12, `.env.example` обновлён

## Planned (следующие 3–5 шагов)

1. **Phase 1 Trust & Polish** — собрать frontend, задеплоить на VDS, smoke `agent-preview` live.
2. **E2E** — landing → agent preview → showcase cards; проверить ChatPage reload с PG.
3. **Phase 2 Agent Builder UX** — wizard создания агента, skills picker, inline test chat, save from preview post-login.
4. **Док-синхронизация** — привести ARCHITECTURE, PROJECT_GUIDE, BRAND к v4 narrative.
5. **Backlog PR** — закрыть выбранные OPEN из TROUBLES (H13, H9) отдельными PR, не блокируя релиз.

См. полный план: [ROADMAP_90_DAYS.md](ROADMAP_90_DAYS.md).
