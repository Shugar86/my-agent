# Security & Production Readiness

> Статус аудита: 2026-05-25. См. также `SERVER.md`, `ARCHITECTURE.md`.

## Матрица рисков

| Проблема | Статус | Реализация |
|----------|--------|------------|
| Rate limiting на Web API | ✅ Исправлено | `slowapi` на эндпоинтах + Redis sliding window (`web/security.py`) для `/api/ask`, `/api/chat*`, workflow run/webhook |
| Авторизация пользователей | ✅ Есть | JWT cookie + `AuthMiddleware`; публичны только landing и GET marketplace |
| Self-modification в production | ✅ Заблокировано | `self_dev` не грузится при `ENV=production` без `ENABLE_SELF_DEV=true` |
| Google Sign-in | ✅ Phase 3 | `/api/auth/google` — отдельные `GOOGLE_AUTH_*` env vars |
| Teams / B2B workspaces | ✅ Phase 3 | Workspaces, invites, RBAC, Analytics UI |
| Bus factor | 🟡 Документировано | Этот файл + `ARCHITECTURE.md` + `SERVER.md` |
| Redis в production | ✅ В compose | `REDIS_URL` в `docker-compose.yml`; startup warning если недоступен |
| `server.log` / `results.json` в git | ✅ Удалено | В `.gitignore`, не коммитить runtime-артефакты |

## Аутентификация

- Логин: `POST /api/login` → JWT в httpOnly cookie `access_token`
- Все `/api/*` (кроме whitelist) требуют cookie
- Публичные маршруты: `web/security.py` → `is_public_path()`
- Marketplace **просмотр** (GET) без логина; install/publish — только с JWT

## Rate limits (Redis, per user или IP)

| Endpoint | Лимит |
|----------|-------|
| `POST /api/ask` | 30/min |
| `POST /api/chat` | 20/min |
| `POST /api/chat/stream` | 20/min |
| `POST /api/workflows/{id}/run` | 10/min |
| `POST /api/workflows/webhook/{id}` | 60/min |

При недоступном Redis лимиты деградируют (slowapi на отдельных route остаётся).

## Self-dev (самомодификация)

Скилл `skills/self_dev/` **отключён** в production:

```bash
ENV=production          # docker-compose уже выставляет
ENABLE_SELF_DEV=false   # явный override для R&D на prod-сервере
```

## Production checklist

1. `cp .env.example .env` — сменить `AGENT_PASSWORD`, `AGENT_SECRET_KEY`
2. `docker compose up -d` — PostgreSQL + Redis + agent
3. Проверить: `curl http://127.0.0.1:8020/api/health`
4. Nginx + TLS перед публичным доступом (`SERVER.md`)
5. Не коммитить `.env`, `*.log`, `results.json`, `data/`

## Onboarding нового инженера

1. Прочитать `ARCHITECTURE.md` (слои: web → core → skills)
2. `SERVER.md` — порты, Docker, тесты
3. Запуск: `.venv/bin/pytest tests/ -v`
4. Frontend: `cd web/frontend && bun run build`
5. Документация: [docs/README.md](docs/README.md) · архив: [docs/archive/README.md](docs/archive/README.md)
