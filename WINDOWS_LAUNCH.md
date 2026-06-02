# Запуск My Agent на Windows

> Краткая справка. Полный индекс: [docs/README.md](docs/README.md).

## Рекомендуется: Docker

```cmd
cd path\to\my-agent
copy .env.example .env
docker compose up -d --build
```

Открыть: http://127.0.0.1:8020/app (логин `admin` / `admin` по умолчанию).

---

## CLI / TUI (без Docker)

### Способ 1: Командная строка

```cmd
cd path\to\my-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python agent.py chat --model fast
python agent.py serve --port 8020
```

### Способ 2: setup.bat

1. Запустите `setup.bat` в корне репозитория.
2. Выберите: ярлык на рабочем столе, PATH или запуск сейчас.

### Способ 3: Ярлык вручную

```
cmd /k cd /d "C:\path\to\my-agent" && .venv\Scripts\activate && python agent.py chat
```

---

## Переменные для live LLM

В `.env` или системных переменных:

```
OPENROUTER_API_KEY=sk-or-v1-...
TAVILY_API_KEY=tvly-...
```

Без ключей чат и публичное demo работают в mock-режиме.

---

## Почему .bat может не работать при двойном клике

- Окно закрывается до чтения ошибки → запускайте из `cmd` или используйте `setup.bat`.
- Python не в PATH → установите Python 3.11+ и отметьте «Add to PATH».
- Неверная рабочая папка → `cd` в каталог с `agent.py` перед запуском.

---

## См. также

- [README.md](README.md) — быстрый старт
- [PROJECT_GUIDE.md](PROJECT_GUIDE.md) — RU-руководство
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — ошибки
