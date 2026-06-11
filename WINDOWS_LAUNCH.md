# Запуск My Agent на Windows

> Версия **3.5.2** · порт web UI: **8020**

---

## Рекомендуется: Docker

```powershell
cd path\to\my-agent
copy .env.example .env
# Заполнить OPENROUTER_API_KEY для live chat (demo работает без ключей)

docker compose up -d --build
start http://127.0.0.1:8020/app
```

Логин по умолчанию: `admin` / `admin` (сменить `AGENT_PASSWORD` в `.env`).

---

## CLI без Docker

### Через командную строку

```cmd
cd path\to\my-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python agent.py chat
python agent.py serve --port 8020
```

### Через `my-agent.bat` / `setup.bat`

1. Дважды кликни `setup.bat` в корне репозитория
2. Выбери: ярлык на рабочем столе, добавление в PATH или запуск сейчас

Если `.bat` закрывается сразу — запускай через `cmd`, чтобы видеть ошибки (Python не в PATH, отсутствует venv и т.д.).

---

## Полезные команды CLI

```cmd
python agent.py --help
python agent.py chat --model fast
python agent.py chat --model balanced
python agent.py list-agents
python agent.py status
python agent.py serve --port 8020
python agent.py test --fast
```

В чате: `/help`, `/exit`, `/clear`, `/model`.

---

## Frontend (если менялся UI)

```cmd
cd web\frontend
bun install
bun run build
```

Собранные файлы попадают в `web/static/app/` — их подхватывает FastAPI.

---

## См. также

- [README.md](README.md) — полный quick start
- [PROJECT_GUIDE.md](PROJECT_GUIDE.md) — RU-руководство
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — типичные ошибки
