# Запуск My Agent на Windows

> CLI и локальный dev. Для полного стека (PostgreSQL, Redis, UI) используйте [Docker](README.md#быстрый-старт-docker) или WSL2.

---

## Быстрый старт

### Способ 1: Командная строка (рекомендуется)

1. Откройте терминал (`Win+R` → `cmd` или PowerShell).
2. Перейдите в каталог репозитория:
   ```cmd
   cd C:\path\to\my-agent
   ```
3. Запустите:
   ```cmd
   python agent.py chat
   ```
   Или с выбором модели:
   ```cmd
   python agent.py chat --model smart
   ```

### Способ 2: `my-agent.bat` / `run.bat`

Дважды кликните `my-agent.bat` в корне репозитория или выполните:

```cmd
run.bat
```

Если окно сразу закрывается — запускайте через `cmd /k run.bat`, чтобы увидеть ошибку (часто Python не в PATH).

### Способ 3: Ярлык на рабочем столе

1. ПКМ на рабочем столе → Создать → Ярлык.
2. Расположение (подставьте свой путь):
   ```
   cmd /k cd /d "C:\path\to\my-agent" && python agent.py chat
   ```
3. Имя: `My Agent`.

---

## Web UI на Windows

Полный продукт (React + FastAPI + PostgreSQL + Redis):

```cmd
docker compose up -d --build
```

Откройте http://localhost:8020/app (логин `admin` / `admin`).

Локально без Docker — см. [README.md](README.md#локальная-разработка).

---

## Полезные команды

```bash
python agent.py --help

python agent.py chat --model fast      # быстрый профиль
python agent.py serve --port 8020      # web-сервер
python agent.py list-agents
python agent.py test --fast            # pytest без slow/docker
```

В чате: `/help`, `/exit`, `/clear`, `/model`.

---

## Переменные окружения

Скопируйте `.env.example` → `.env` и задайте минимум:

| Переменная | Назначение |
|------------|------------|
| `OPENROUTER_API_KEY` | Primary LLM для live chat |
| `TAVILY_API_KEY` | Веб-поиск (опционально) |
| `AGENT_PASSWORD` | Пароль админа |

---

## Типичные проблемы

| Симптом | Решение |
|---------|---------|
| `python` не найден | Установите Python 3.11+ с [python.org](https://www.python.org/downloads/) и отметьте «Add to PATH» |
| `.bat` закрывается мгновенно | Запуск через `cmd /k` или PowerShell из каталога проекта |
| Порт 8020 занят | `netstat -ano \| findstr :8020` → завершить процесс или сменить порт |
| 500 в чате | Проверить `OPENROUTER_API_KEY` в `.env` — см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |

См. также [PROJECT_GUIDE.md](PROJECT_GUIDE.md) и [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
