# Запуск My Agent на Windows

> CLI и локальная разработка. Для production используйте Docker — см. [README.md](README.md).

Замените `%REPO%` на путь к клону репозитория (например `C:\Projects\my-agent`).

---

## Быстрый старт

### Способ 1: Командная строка (рекомендуется)

```cmd
cd /d %REPO%
python agent.py chat
```

С профилем модели:

```cmd
python agent.py chat --model balanced
```

### Способ 2: setup.bat

1. Дважды кликните `setup.bat` в корне репозитория.
2. Выберите опцию:
   - **1** — создать ярлык на рабочем столе
   - **2** — добавить в PATH
   - **3** — запустить сейчас

### Способ 3: Ярлык вручную

1. Правый клик на рабочем столе → Создать → Ярлык
2. Расположение:
   ```
   cmd /k cd /d "%REPO%" && python agent.py chat
   ```
3. Имя: `My Agent`

---

## Веб-интерфейс

```cmd
cd /d %REPO%
python agent.py serve --port 8020
```

Откройте http://127.0.0.1:8020/app

Или через Docker (предпочтительно):

```cmd
docker compose up -d --build
```

---

## Полезные команды

```cmd
python agent.py --help
python agent.py chat --model fast
python agent.py chat --model smart
python agent.py status
python agent.py list-agents
python agent.py chat --agent developer
```

Профили моделей: `core/configurator.py` (`fast`, `balanced`, `smart`, `kimi`, `local`).

---

## Добавление в PATH

```powershell
# PowerShell (от администратора)
[Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";%REPO%",
    "User"
)
```

После этого из любой папки:

```cmd
my-agent.bat
```

Или используйте `my-agent.bat` / `run.bat` из корня репозитория.

---

## Почему .bat может не работать при двойном клике

- Python не в PATH
- Окно закрывается до чтения ошибки
- Неверная кодировка консоли

**Решение:** запускайте через `cmd` или `setup.bat`.

См. также: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
