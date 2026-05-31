# Запуск My Agent на Windows

> CLI и локальный web. Полное RU-руководство: [PROJECT_GUIDE.md](PROJECT_GUIDE.md).  
> Production: [DEPLOYMENT.md](DEPLOYMENT.md) (Docker на Linux/VDS предпочтительнее).

---

## Быстрый старт

### Способ 1: Командная строка (рекомендуется)

```cmd
cd C:\path\to\my-agent
python agent.py chat
```

С профилем модели:

```cmd
python agent.py chat --model smart
```

### Способ 2: setup.bat

1. Дважды кликните `setup.bat` в корне репозитория.
2. Выберите:
   - **1** — ярлык на рабочем столе
   - **2** — добавить в PATH
   - **3** — запустить сейчас

### Способ 3: Ярлык вручную

Создайте ярлык с командой:

```text
cmd /k cd /d "C:\path\to\my-agent" && python agent.py chat
```

---

## Web UI на Windows

```cmd
cd C:\path\to\my-agent
copy .env.example .env
REM Заполните OPENROUTER_API_KEY для live chat

python -m uvicorn web.server:app --host 0.0.0.0 --port 8020
```

Откройте http://127.0.0.1:8020/app (логин по умолчанию: `admin` / `admin`).

Frontend (после изменений UI):

```cmd
cd web\frontend
bun install
bun run build
```

---

## Полезные команды CLI

```cmd
python agent.py --help
python agent.py chat --model fast
python agent.py chat --model balanced
python agent.py status
python agent.py serve --port 8020
python agent.py chat --agent developer
```

---

## Почему .bat может не работать при двойном клике

- Python не в PATH
- Окно закрывается до вывода ошибки
- Неверная кодировая страница

**Решение:** запускайте через `cmd` или `setup.bat`.

---

## Добавление в PATH (PowerShell, от пользователя)

```powershell
[Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";C:\path\to\my-agent",
    "User"
)
```

После перезапуска терминала:

```cmd
python agent.py chat
```

---

## См. также

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — ошибки chat, Redis, порт 8020
- [docs/README.md](docs/README.md) — индекс документации
