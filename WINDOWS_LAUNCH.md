# Запуск My Agent на Windows

> CLI и локальная разработка. Для полного стека (PostgreSQL, Redis, Web UI) используйте **Docker** — см. [README.md](README.md).

---

## Рекомендуемый способ: Docker Desktop

```powershell
cd C:\path\to\my-agent
copy .env.example .env
docker compose up -d --build
```

Откройте http://localhost:8020/app (логин: `admin` / `admin`).

---

## CLI без Docker

### Требования

- Python 3.11+
- Git Bash или PowerShell

### Быстрый старт

```cmd
cd C:\path\to\my-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

python agent.py chat --model balanced
```

Или через `my-agent.bat` / `run.bat` в корне репозитория.

### Полезные команды

```bash
python agent.py chat                    # интерактивный чат
python agent.py chat --model fast       # быстрый профиль
python agent.py chat --model smart      # Claude Sonnet via OpenRouter
python agent.py chat --agent developer  # конкретный агент
python agent.py serve --port 8020       # web-сервер
python agent.py status                  # статус системы
python agent.py test --fast             # быстрые тесты
```

Профили моделей: `core/configurator.py` (`fast`, `balanced`, `smart`, `kimi`, `local`).

---

## Ярлык на рабочем столе

1. Правый клик → Создать → Ярлык
2. Расположение:
   ```
   cmd /k cd /d "C:\path\to\my-agent" && .venv\Scripts\activate && python agent.py chat
   ```
3. Назовите «My Agent»

---

## Почему .bat может не работать при двойном клике

- Python не в PATH → используйте полный путь к `.venv\Scripts\python.exe`
- Окно закрывается сразу → добавьте `pause` в конец `.bat`
- Неверная кодировка → запускайте через `cmd`, не Explorer

---

## См. также

- [README.md](README.md) — полный quick start
- [PROJECT_GUIDE.md](PROJECT_GUIDE.md) — RU-руководство
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — типичные ошибки
