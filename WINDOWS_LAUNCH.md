# Запуск My Agent на Windows

> Порт по умолчанию: **8020** (не 8000). Документация: [docs/README.md](docs/README.md).

## Рекомендуемый способ — Docker Desktop

```powershell
cd path\to\my-agent
copy .env.example .env
# Заполнить OPENROUTER_API_KEY (опционально для live chat)

docker compose up -d --build
start http://127.0.0.1:8020/showcase#playground
```

Логин: `admin` / `admin` (сменить `AGENT_PASSWORD` в `.env`).

---

## CLI без Docker

### Требования

- Python 3.11+
- PostgreSQL и Redis (или `docker compose up db redis -d`)

### Запуск

```powershell
cd path\to\my-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

Frontend (один раз или после изменений UI):

```powershell
cd web\frontend
bun install
bun run build
```

### Полезные команды CLI

```powershell
python agent.py chat
python agent.py chat --model fast
python agent.py serve --port 8020
python agent.py list-agents
python agent.py status
```

---

## Через .bat-файлы

| Файл | Назначение |
|------|------------|
| `run.bat` | Запуск web-сервера |
| `my-agent.bat` | CLI-обёртка |
| `setup.bat` | Ярлык / PATH / быстрый старт |

При двойном клике `.bat` может не найти Python — запускайте из терминала или используйте Docker.

---

## Troubleshooting (Windows)

| Проблема | Решение |
|----------|---------|
| Порт занят | `netstat -ano \| findstr :8020` → завершить процесс |
| 500 в чате | Проверить `OPENROUTER_API_KEY` в `.env` |
| Redis недоступен | `docker compose up redis -d` |
| Кодировка в консоли | `chcp 65001` перед запуском |

Подробнее: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
