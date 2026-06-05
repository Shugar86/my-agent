# Запуск My Agent на Windows

> Для полного стека (PostgreSQL, Redis, React UI) используйте [Docker](README.md#быстрый-старт-docker) или WSL2.  
> Этот файл — **CLI/TUI** через `agent.py` без контейнеров.

---

## Требования

- Python 3.11+
- Репозиторий клонирован локально (например `C:\dev\my-agent`)

```powershell
cd C:\dev\my-agent
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Заполните OPENROUTER_API_KEY для live-ответов в чате
```

---

## Быстрый старт

### Способ 1: Командная строка (рекомендуется)

```cmd
cd C:\dev\my-agent
.\.venv\Scripts\activate
python agent.py chat
```

С профилем модели:

```cmd
python agent.py chat --model smart
```

### Способ 2: setup.bat

1. Дважды кликните `setup.bat` в корне репозитория.
2. Выберите: ярлык на рабочий стол, добавление в PATH или запуск сейчас.

### Способ 3: Ярлык вручную

Цель ярлыка:

```text
cmd /k cd /d "C:\dev\my-agent" && .\.venv\Scripts\activate && python agent.py chat
```

---

## Веб-интерфейс на Windows

```cmd
python agent.py serve --port 8020
```

Или после сборки frontend (`cd web\frontend && bun run build`):

```cmd
python -m uvicorn web.server:app --host 0.0.0.0 --port 8020
```

Откройте http://127.0.0.1:8020/app (логин по умолчанию: `admin` / `admin`).

Порт **8020** — тот же, что в Docker/VDS (не 8000).

---

## Полезные команды

```bash
python agent.py --help
python agent.py chat --model fast
python agent.py chat --agent developer
python agent.py list-agents
python agent.py test --fast
```

В TUI-чате: `/help`, `/exit`, `/clear`, `/model`.

---

## Если .bat не запускается по двойному клику

- Python не в PATH → используйте venv: `.\.venv\Scripts\python.exe agent.py chat`
- Окно закрывается сразу → запускайте из `cmd`, не двойным кликом
- Кодировка → `chcp 65001` перед запуском

Подробнее: [PROJECT_GUIDE.md](PROJECT_GUIDE.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
