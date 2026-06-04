# Security & Production Readiness

> Статус: **v3.5.2** · 2026-06-04. См. также `SERVER.md`, `ARCHITECTURE.md`.

## Матрица рисков

| Проблема | Статус | Реализация |
|----------|--------|------------|
| Rate limiting на Web API | ✅ Исправлено | `slowapi` + Redis sliding window (`web/security.py`) |
| Авторизация пользователей | ✅ Есть | JWT cookie + `AuthMiddleware`; публичны landing и GET marketplace |
| Self-modification в production | ✅ Заблокировано | `self_dev` не грузится при `ENV=production` без `ENABLE_SELF_DEV=true` |
| Google Sign-in | ✅ | `/api/auth/google` — `GOOGLE_AUTH_*` env vars |
| Teams / B2B workspaces | ✅ | Workspaces, invites, RBAC, Analytics UI |
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
2. Задать `OPENROUTER_API_KEY` для live chat (demo работает без ключей)
3. `docker compose up -d` — PostgreSQL + Redis + agent
4. Проверить: `curl http://127.0.0.1:8020/api/health` → `"redis": true`
5. Nginx + TLS перед публичным доступом (`SERVER.md`)
6. Не коммитить `.env`, `*.log`, `results.json`, `data/`

## Onboarding нового инженера

1. [ARCHITECTURE.md](ARCHITECTURE.md) — слои: web → core → skills
2. [HANDOFF.md](HANDOFF.md) — текущее состояние продукта
3. [SERVER.md](SERVER.md) — порты, Docker, тесты
4. Запуск: `pytest tests/ -q`
5. Frontend: `cd web/frontend && bun run build`
6. Индекс: [docs/README.md](docs/README.md)
