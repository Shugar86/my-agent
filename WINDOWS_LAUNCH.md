# Запуск My Agent на Windows

## Быстрый старт (3 способа)

### Способ 1: Через командную строку (РЕКОМЕНДУЕТСЯ)

1. Открой терминал (Win+R → `cmd` → Enter)
2. Перейди в папку агента:
   ```cmd
   cd "C:\Users\Тема\Desktop\moy agent\my-agent"
   ```
3. Запусти:
   ```cmd
   python agent.py
   ```
   Или с выбором модели:
   ```cmd
   python agent.py --model smart
   ```

### Способ 2: Через setup.bat

1. Дважды кликни `setup.bat`
2. Выбери опцию:
   - **1** — Создать ярлык на рабочем столе
   - **2** — Добавить в PATH (можно запускать из любой папки)
   - **3** — Просто запустить сейчас

### Способ 3: Ярлык вручную

1. Правый клик на рабочем столе → Создать → Ярлык
2. В поле "Укажите расположение" введи:
   ```
   cmd /k cd /d "C:\Users\Тема\Desktop\moy agent\my-agent" && python agent.py chat
   ```
3. Назови ярлык "My Agent"
4. Готово! Двойной клик открывает TUI.

## Почему .bat может не работать при двойном клике

При двойном клике по `.bat` файл Windows может:
- Не найти Python (если он не в PATH)
- Закрыть окно слишком быстро
- Использовать неправильную кодировку

**Решение:** Используй `setup.bat` или запускай через командную строку.

## Полезные команды

```bash
# Интерактивный чат (по умолчанию)
python agent.py
python agent.py chat

# С конкретной моделью
python agent.py chat --model fast      # Быстрая
python agent.py chat --model smart     # Умная
python agent.py chat --model balanced  # Сбалансированная

# Статус системы
python agent.py status

# Веб-сервер
python agent.py serve

# Запуск конкретного агента
python agent.py chat --agent developer
```

## Добавление в PATH (для запуска из любой папки)

```powershell
# PowerShell (от админа)
[Environment]::SetEnvironmentVariable(
    "Path", 
    $env:Path + ";C:\Users\Тема\Desktop\moy agent\my-agent", 
    "User"
)
```

После этого можно просто писать в любом терминале:
```cmd
agent
agent --model smart
```
