# Запуск My Agent на Windows

> Краткая инструкция. Полный индекс: [docs/README.md](docs/README.md).

---

## Рекомендуется: Docker Desktop

```powershell
cd C:\path\to\my-agent
copy .env.example .env
# Заполните OPENROUTER_API_KEY при необходимости live-чата

docker compose up -d --build
```

Откройте в браузере: **http://127.0.0.1:8020/app** (логин `admin` / `admin` по умолчанию).

Demo без login: **http://127.0.0.1:8020/showcase#playground**

---

## CLI без Docker

Требования: Python 3.11+, PostgreSQL и Redis (или только `docker compose up db redis -d`).

```powershell
cd C:\path\to\my-agent
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

$env:DATABASE_URL="postgresql://agent:agentpass@127.0.0.1:5437/agent_db"
$env:REDIS_URL="redis://127.0.0.1:6380/0"

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020
```

Frontend (после изменений UI):

```powershell
cd web\frontend
bun install
bun run build
```

---

## Интерактивный TUI

```powershell
python agent.py chat
python agent.py chat --model fast
python agent.py serve --port 8020
python agent.py --help
```

В чате: `/help`, `/exit`, `/clear`, `/model`.

---

## setup.bat (опционально)

В корне репозитория есть `setup.bat`:

1. Создать ярлык на рабочем столе  
2. Добавить папку в PATH  
3. Запустить агента сразу  

Если `.bat` закрывается при двойном клике — запускайте из **cmd** или **PowerShell**, чтобы видеть ошибки (Python не в PATH и т.п.).

---

## См. также

- [README.md](README.md) — порты и маршруты  
- [PROJECT_GUIDE.md](PROJECT_GUIDE.md) — RU-руководство  
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — типичные ошибки  
