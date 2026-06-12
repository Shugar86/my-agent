# Запуск My Agent на Windows

> Рекомендуется **Docker Desktop** — одинаковый стек с Linux/VDS. CLI ниже — для локальной разработки.

---

## Docker (рекомендуется)

1. Установи [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Клонируй репозиторий и перейди в папку проекта
3. Запусти:

```cmd
copy .env.example .env
docker compose up -d --build
```

Открой http://localhost:8020/showcase#playground

Подробнее: [README.md](README.md), [DEPLOYMENT.md](DEPLOYMENT.md).

---

## CLI без Docker

### Требования

- Python 3.11+
- Git Bash или PowerShell

### Быстрый старт

```cmd
cd path\to\my-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

Frontend (нужен [Bun](https://bun.sh) или Node 20+):

```cmd
cd web\frontend
bun install && bun run build
```

### Через agent.py

```cmd
python agent.py chat --model balanced
python agent.py serve --port 8020
python agent.py status
python agent.py chat --agent developer
```

### my-agent.bat

Дважды кликни `my-agent.bat` или `run.bat` в корне репозитория — откроется интерактивный чат (если Python в PATH).

---

## Полезные команды

```cmd
python agent.py --help
python agent.py list-agents
python agent.py test --fast
```

Профили моделей: `balanced` (OpenRouter), `fast`, `smart`, `kimi`, `local` — см. `core/configurator.py`.

---

## Типичные проблемы

| Проблема | Решение |
|----------|---------|
| `.bat` закрывается сразу | Запускай из `cmd`, не двойным кликом |
| Python не найден | Добавь Python в PATH или используй полный путь |
| Порт 8020 занят | `netstat -ano \| findstr :8020` → завершить процесс |
| 500 в чате | Задай `OPENROUTER_API_KEY` в `.env` |

Полный список: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
