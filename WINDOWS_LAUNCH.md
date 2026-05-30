# Запуск My Agent на Windows

> Без Docker: CLI / TUI. Для полного стека (PostgreSQL, Redis, React UI) используйте [README.md](README.md) (Docker) или WSL2.

---

## Быстрый старт

### 1. Командная строка (рекомендуется)

```cmd
cd C:\path\to\my-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python agent.py chat
```

### 2. setup.bat

В корне репозитория: двойной клик `setup.bat` → создать ярлык, добавить в PATH или запустить сразу.

### 3. Ярлык

Цель ярлыка:

```text
cmd /k cd /d "C:\path\to\my-agent" && .venv\Scripts\activate && python agent.py chat
```

---

## Полезные команды

```bash
python agent.py --help
python agent.py chat --model fast
python agent.py chat --model balanced
python agent.py serve --port 8020
python agent.py list-agents
python agent.py test --fast
```

В чате: `/help`, `/exit`, `/clear`, `/model`.

Профили моделей: `config/models.yaml`.

---

## Веб-интерфейс на Windows

1. Установите [Docker Desktop](https://www.docker.com/products/docker-desktop/) или поднимите PostgreSQL + Redis вручную.
2. Скопируйте `.env.example` → `.env`, задайте `OPENROUTER_API_KEY` для live chat.
3. `docker compose up -d --build` → http://localhost:8020/

Подробнее: [PROJECT_GUIDE.md](PROJECT_GUIDE.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Частые проблемы

| Симптом | Решение |
|---------|---------|
| `.bat` закрывается сразу | Запускайте через `cmd`, не двойным кликом |
| Python не найден | Установите Python 3.11+, отметьте «Add to PATH» |
| Порт 8020 занят | `netstat -ano \| findstr :8020` → завершить PID |

Полный список: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
