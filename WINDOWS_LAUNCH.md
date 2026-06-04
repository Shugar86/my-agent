# Запуск My Agent на Windows

> Версия **3.5.2** · порт **8020**

---

## Рекомендуется: Docker

```powershell
cd C:\path\to\my-agent
copy .env.example .env
docker compose up -d --build
```

Открыть: http://localhost:8020/showcase#playground

---

## CLI (без Docker)

### 1. Подготовка

```powershell
cd C:\path\to\my-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### 2. Запуск

```powershell
# Интерактивный чат
python agent.py chat

# С конкретной моделью
python agent.py chat --model fast
python agent.py chat --model balanced

# Web-сервер
python agent.py serve --port 8020
# или
python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

Открыть: http://localhost:8020/app (login: `admin` / `admin` по умолчанию).

### 3. Frontend (после изменений UI)

```powershell
cd web\frontend
bun install
bun run build
```

---

## Полезные команды

```powershell
python agent.py --help
python agent.py list-agents
python agent.py status
python agent.py test --fast
python agent.py chat --agent developer
```

---

## Типичные проблемы Windows

| Проблема | Решение |
|----------|---------|
| Python не найден | Установить Python 3.11+ и добавить в PATH |
| `.bat` закрывается сразу | Запускать через `cmd` или PowerShell |
| `UnicodeEncodeError` | `set PYTHONIOENCODING=utf-8` |
| Кириллица в пути проекта | Переместить в ASCII-путь, напр. `C:\dev\my-agent` |
| Порт 8020 занят | `netstat -ano \| findstr :8020` → завершить процесс |

Подробнее: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## См. также

- [README.md](README.md) — quick start
- [PROJECT_GUIDE.md](PROJECT_GUIDE.md) — RU-руководство
- [DEPLOYMENT.md](DEPLOYMENT.md) — деплой
