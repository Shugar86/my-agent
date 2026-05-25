# My Agent — развёртывание на VDS

> Сервер: `159.195.31.95` | Путь: `/opt/projects/my-agent/`  
> Статус: **R&D** (не в корневом `docker-compose.yml`)

---

## Порты (этот сервер)

| Сервис | Host | Контейнер | Конфликты |
|--------|------|-----------|-----------|
| Web UI | `127.0.0.1:8020` | 8020 | ❌ 8000 занят magikbook-api |
| PostgreSQL | `127.0.0.1:5437` | 5432 | ❌ 5436 infodon, 5435 coffeeman |
| Redis | `127.0.0.1:6380` | 6379 | magikbook-redis без host-порта |

---

## Быстрый старт (Docker)

```bash
cd /opt/projects/my-agent

# 1. Конфиг
cp .env.example .env
# Заполнить OPENROUTER_API_KEY, AGENT_SECRET_KEY, AGENT_PASSWORD

# 2. Собрать frontend (если менялся web/frontend/)
cd web/frontend && npm install && npm run build && cd ../..

# 3. Seed workflow-шаблонов (первый раз)
python3 scripts/seed_workflow_templates.py

# 4. Запуск
docker compose up -d --build

# 5. Проверка
curl -s http://127.0.0.1:8020/api/health | python3 -m json.tool
```

Логин по умолчанию: `admin` / значение `AGENT_PASSWORD` из `.env`.

---

## Локальная разработка (без Docker)

```bash
cd /opt/projects/my-agent
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # заполнить ключи

# Миграции + seed
.venv/bin/python scripts/seed_workflow_templates.py

# Dev-сервер
.venv/bin/uvicorn web.server:app --host 127.0.0.1 --port 8020 --reload
```

UI: http://127.0.0.1:8020/  
Workflow Builder: http://127.0.0.1:8020/workflows

---

## Nginx (опционально, публичный доступ)

```nginx
# /etc/nginx/sites-available/my-agent
server {
    listen 80;
    server_name agent.example.com;

    location / {
        proxy_pass http://127.0.0.1:8020;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

---

## Тесты

```bash
cd /opt/projects/my-agent
.venv/bin/python -m pytest tests/test_workflow_engine.py tests/test_marketplace.py -v
```

---

## Структура Phase 1

| Компонент | Путь |
|-----------|------|
| Workflow Engine | `core/workflow/` |
| API routes | `web/workflow_router.py` |
| React Flow UI | `web/frontend/` → `web/static/workflow/` |
| Шаблоны (12 шт.) | `scripts/seed_workflow_templates.py` |
| Миграции | `alembic/versions/002_workflows.py` |

Документация продукта: `ROADMAP_90_DAYS.md`, `ARCHITECTURE.md`, `DEPLOYMENT.md`.
