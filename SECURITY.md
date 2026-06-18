# Security & Production Readiness

> Статус аудита: 2026-05-27 (re-audit post-remediation). См. также `TROUBLES.md`, `SERVER.md`, `ARCHITECTURE.md`.

## Матрица рисков

| Проблема | Статус | Реализация |
|----------|--------|------------|
| Rate limiting на Web API | ✅ Исправлено | `slowapi` + `get_client_ip()` (X-Forwarded-For / X-Real-IP) + Redis sliding window |
| CORS в production | ✅ Исправлено | localhost defaults + `CORS_ORIGINS` env ([web/server.py](web/server.py)) |
| JS code execution (RCE) | ✅ Исправлено | Docker file mount (`run_javascript`), без `bash -c` |
| File tools path traversal | ✅ Исправлено | `AGENT_WORKSPACE` + `validate_safe_path_or_error` |
| Default admin password | ✅ Исправлено | Prod: `AGENT_PASSWORD` ≥ 12 chars или bootstrap fail; wizard rejects short passwords |
| Secrets in git | ✅ CI gate | `scripts/check-secrets.sh`, `.github/workflows/secrets-check.yml` |
| Import-time server crash | ✅ Исправлено | `load_all_keys_to_env()` / AgentStore в `_init_agent_runtime()` на startup |
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

1. `cp .env.example .env` — `AGENT_PASSWORD` (≥ 12 символов), `AGENT_SECRET_KEY`, `CORS_ORIGINS`
2. `docker compose up -d` — PostgreSQL + Redis + agent
3. Проверить: `curl http://127.0.0.1:8020/api/health`
4. Nginx/Caddy + TLS перед публичным доступом (`SERVER.md`, `deploy/Caddyfile.prod`)
5. Не коммитить `.env`, `*.log`, `results.json`, `data/`
6. Gate локально: `bash scripts/check-secrets.sh` + pytest gate (см. `TROUBLES.md`)

### Code execution in Docker

`execute_code` вызывает Docker на хосте. В prod-контейнере agent нужен доступ к daemon (например volume `/var/run/docker.sock`) — иначе tools python/js/bash вернут ошибку. Альтернатива: отключить tool на prod без sandbox.

## Verification gate

```bash
cd my-agent && source .venv/bin/activate
uv build && bash scripts/check-secrets.sh
pytest tests/test_code_tools.py tests/test_file_tools.py \
       tests/test_security_improvements.py tests/test_async_utils.py \
       tests/test_db_manager.py tests/test_production_hardening.py \
       tests/test_all.py::test_memory_manager -q
```

## Onboarding нового инженера

1. Прочитать `ARCHITECTURE.md` (слои: web → core → skills)
2. `SERVER.md` — порты, Docker, тесты
3. Запуск: `.venv/bin/pytest tests/ -v`
4. Frontend: `cd web/frontend && bun run build`
5. Документация: [docs/README.md](docs/README.md) · roadmap: [ROADMAP_90_DAYS.md](ROADMAP_90_DAYS.md) · статус: [STATE.md](STATE.md)
