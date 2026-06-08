# Запуск My Agent на Windows

> Рекомендуемый путь — **Docker Desktop** (см. [README.md](README.md)).  
> Ниже — альтернативы через CLI без Docker.

---

## Способ 1: Docker Desktop (рекомендуется)

1. Установи [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Клонируй репозиторий и открой папку в терминале
3. Запусти:

```cmd
copy .env.example .env
docker compose up -d --build
```

4. Открой http://127.0.0.1:8020/app (логин: `admin` / `admin`)

---

## Способ 2: CLI (Python)

1. Установи Python 3.11+ с [python.org](https://www.python.org/downloads/) (галочка «Add to PATH»)
2. В терминале перейди в корень репозитория:

```cmd
cd путь\к\my-agent
```

3. Создай venv и установи зависимости:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

4. Запусти web-сервер:

```cmd
python -m uvicorn web.server:app --host 0.0.0.0 --port 8020
```

Или интерактивный чат:

```cmd
python agent.py chat
```

---

## Способ 3: setup.bat / my-agent.bat

В корне репозитория:

- `setup.bat` — создать ярлык, добавить в PATH или запустить сейчас
- `my-agent.bat` — быстрый запуск CLI

Если `.bat` закрывается сразу — запускай через `cmd`, а не двойным кликом.

---

## Полезные команды

```cmd
python agent.py chat --model fast
python agent.py serve --port 8020
python agent.py list-agents
python agent.py status
```

Профили моделей: `config/agent.json` + `core/configurator.py` (не `config/models.yaml`).

---

## Frontend (если меняешь UI)

```cmd
cd web\frontend
bun install
bun run build
```

Bun: https://bun.sh — или используй `npm install && npm run build`.

---

## См. также

- [README.md](README.md) — полный quick start
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — типичные ошибки
- [PROJECT_GUIDE.md](PROJECT_GUIDE.md) — RU-руководство
