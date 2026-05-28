# Запуск My Agent на Windows

> Для production и demo предпочтителен **Docker** — см. [README.md](README.md).  
> Этот файл — только для локального CLI без контейнеров.

---

## Требования

- Python 3.11+
- Git clone репозитория в любую папку (ниже — `%REPO%` как корень проекта)

---

## Быстрый старт

### 1. Командная строка (рекомендуется)

```cmd
cd /d "%REPO%"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python agent.py chat
```

### 2. Через `my-agent.bat` / `run.bat`

Дважды кликнуть `my-agent.bat` в корне репозитория или:

```cmd
cd /d "%REPO%"
my-agent.bat
```

Если окно сразу закрывается — запускайте из `cmd`, чтобы видеть ошибки (часто Python не в PATH).

### 3. Web-сервер на Windows

```cmd
cd /d "%REPO%"
.venv\Scripts\activate
python -m uvicorn web.server:app --host 0.0.0.0 --port 8020
```

Открыть: http://127.0.0.1:8020/app (нужны PostgreSQL + Redis или Docker только для `db`/`redis`).

---

## Полезные команды CLI

```cmd
python agent.py chat --model fast
python agent.py chat --model balanced
python agent.py serve --port 8020
python agent.py list-agents
python agent.py status
python agent.py chat --agent developer
```

Профили моделей: `config/models.yaml`.

---

## Переменные окружения

Скопируйте `.env.example` → `.env` и задайте минимум:

```
OPENROUTER_API_KEY=sk-or-v1-...
DATABASE_URL=postgresql://agent:agentpass@127.0.0.1:5437/agent_db
REDIS_URL=redis://127.0.0.1:6380/0
```

Без ключей работает публичный mock-demo: http://127.0.0.1:8020/showcase#playground

---

## Типичные проблемы

| Симптом | Решение |
|---------|---------|
| `python` не найден | Установить Python 3.11+, добавить в PATH |
| Порт 8020 занят | `netstat -ano \| findstr :8020` → завершить PID |
| 500 в чате | Проверить `OPENROUTER_API_KEY`, см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |

Полный гайд: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) · [PROJECT_GUIDE.md](PROJECT_GUIDE.md)
