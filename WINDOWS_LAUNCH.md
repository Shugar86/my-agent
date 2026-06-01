# Запуск My Agent на Windows

> CLI и локальный web. Для полного стека (PostgreSQL, Redis) удобнее [Docker](README.md#быстрый-старт-docker).

Замените `%MY_AGENT_ROOT%` на путь к клону репозитория (например `C:\dev\my-agent`).

---

## Быстрый старт

### Способ 1: Командная строка (рекомендуется)

1. Win+R → `cmd` → Enter
2. Перейти в репозиторий:
   ```cmd
   cd /d "%MY_AGENT_ROOT%"
   ```
3. Запуск:
   ```cmd
   python agent.py chat
   ```
   С профилем модели:
   ```cmd
   python agent.py chat --model balanced
   ```

### Способ 2: `my-agent.bat` / `setup.bat`

В корне репозитория:

- **`my-agent.bat`** — быстрый запуск CLI
- **`setup.bat`** — ярлык на рабочий стол, PATH, или разовый запуск

### Способ 3: Ярлык вручную

1. Рабочий стол → Создать → Ярлык
2. Расположение:
   ```text
   cmd /k cd /d "%MY_AGENT_ROOT%" && python agent.py chat
   ```
3. Имя: `My Agent`

---

## Web UI на Windows

```cmd
cd /d "%MY_AGENT_ROOT%"
copy .env.example .env
REM Заполнить OPENROUTER_API_KEY при необходимости live chat

docker compose up -d --build
```

Открыть: http://127.0.0.1:8020/app (логин `admin` / `admin` по умолчанию).

Без Docker — только API (нужны PostgreSQL и Redis, см. [PROJECT_GUIDE.md](PROJECT_GUIDE.md)):

```cmd
python -m uvicorn web.server:app --host 0.0.0.0 --port 8020 --reload
```

Frontend: `cd web\frontend && bun run build` (или `npm run build`).

---

## Полезные команды

```cmd
python agent.py --help
python agent.py chat --model fast
python agent.py serve --port 8020
python agent.py list-agents
python agent.py test --fast
```

---

## Добавление в PATH

PowerShell (от имени пользователя):

```powershell
$root = "C:\dev\my-agent"   # ваш путь
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$root", "User")
```

После перезапуска терминала:

```cmd
cd /d %MY_AGENT_ROOT%
python agent.py chat
```

---

## Если `.bat` не работает при двойном клике

- Python не в `PATH` — установите Python 3.11+ и отметьте «Add to PATH»
- Окно сразу закрывается — запускайте из `cmd` или используйте `setup.bat`
- Кодировка консоли — `chcp 65001` перед запуском

Подробнее: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) · индекс: [docs/README.md](docs/README.md).
