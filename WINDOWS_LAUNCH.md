# Запуск My Agent на Windows

> Версия **3.5.3** · см. также [README.md](README.md) и [PROJECT_GUIDE.md](PROJECT_GUIDE.md).

---

## Способ 1: Docker (рекомендуется)

Требуется [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```powershell
cd C:\path\to\my-agent
copy .env.example .env
# Заполнить OPENROUTER_API_KEY (опционально для live chat)

docker compose up -d --build
start http://127.0.0.1:8020/showcase#playground
```

Логин: `admin` / `admin` (сменить `AGENT_PASSWORD` в `.env`).

---

## Способ 2: CLI (Python)

1. Установить Python 3.11+ и добавить в PATH.
2. Открыть терминал (Win+R → `cmd` → Enter).
3. Перейти в каталог репозитория:

```cmd
cd C:\path\to\my-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

4. Запуск:

```cmd
python agent.py chat
python agent.py chat --model balanced
python agent.py serve --port 8020
```

Или через `my-agent.bat` / `run.bat` в корне репозитория.

---

## Способ 3: setup.bat

1. Дважды кликнуть `setup.bat`.
2. Выбрать опцию:
   - **1** — ярлык на рабочем столе
   - **2** — добавить в PATH
   - **3** — запустить сейчас

При создании ярлыка укажите путь к **вашему** каталогу `my-agent`, не копируйте чужой абсолютный путь.

---

## Полезные команды

```cmd
python agent.py chat --model fast       REM быстрый профиль
python agent.py chat --model smart      REM умный профиль
python agent.py chat --agent developer  REM конкретный агент
python agent.py status
python agent.py test --fast
```

---

## Почему .bat может не работать при двойном клике

- Python не в PATH → установить Python 3.11+ с галочкой «Add to PATH»
- Окно закрывается сразу → запускать через `cmd`, не двойным кликом
- Кодировка → предпочитать PowerShell или `setup.bat`

---

## Frontend (опционально)

Для сборки React UI нужен [Bun](https://bun.sh/) или Node 20+:

```powershell
cd web\frontend
bun install
bun run build
```

Dev-режим с hot reload: `bun run dev` (proxy на `:8020`).
