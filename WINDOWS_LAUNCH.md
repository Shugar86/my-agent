# Запуск My Agent на Windows

> Краткая инструкция. Полный индекс: [docs/README.md](docs/README.md).

## Рекомендуется: Docker Desktop

1. Установите [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. В PowerShell или cmd перейдите в каталог клона репозитория:

```cmd
cd C:\path\to\my-agent
copy .env.example .env
docker compose up -d --build
```

3. Откройте http://127.0.0.1:8020/app (логин `admin` / `admin` по умолчанию).

Каноническое demo без входа: http://127.0.0.1:8020/showcase#playground

---

## Локально: Python CLI

Требования: Python 3.11+, зависимости из `requirements.txt`.

```cmd
cd C:\path\to\my-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python agent.py chat
```

Полезные команды:

```cmd
python agent.py --help
python agent.py chat --model fast
python agent.py serve --port 8020
python agent.py list-agents
python agent.py test --fast
```

Веб-интерфейс после `serve` или uvicorn: http://127.0.0.1:8020/app

---

## Скрипты в репозитории

| Файл | Назначение |
|------|------------|
| `my-agent.bat` | Быстрый запуск CLI |
| `run.bat` | Альтернативный launcher |
| `setup.bat` | Ярлык / PATH (если есть в вашей копии) |

При двойном клике по `.bat` окно может закрыться до чтения ошибки — запускайте из терминала.

---

## Типичные проблемы

| Симптом | Решение |
|---------|---------|
| `python` не найден | Добавьте Python в PATH или используйте `py -3.11` |
| Порт занят | Проект использует **8020**, не 8000 |
| Нет ответа в чате | Задайте `OPENROUTER_API_KEY` в `.env`, перезапустите контейнер |

Подробнее: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
