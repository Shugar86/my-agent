# Как участвовать в My Agent

My Agent — персональный продукт экосистемы Shugar86, но открыт для идей, issue и PR. Если хотите помочь — сначала обсудите изменение в issues, чтобы не тратить время на конфликт с roadmap.

<!-- badge-линия -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://www.conventionalcommits.org/)
[![Code of Conduct](https://img.shields.io/badge/Code%20of%20Conduct-professional-blue.svg)](./AGENTS.md)

---

## Быстрый путь

1. **Форкните** репозиторий.
2. **Создайте ветку:**

   ```bash
   git checkout -b feature/короткое-описание
   ```

3. **Сделайте изменения** — минимальный diff, KISS.
4. **Запустите тесты и проверку секретов:**

   ```bash
   pytest tests/test_code_tools.py tests/test_file_tools.py \
          tests/test_security_improvements.py tests/test_async_utils.py -q
   bash scripts/check-secrets.sh
   ```

5. **Откройте PR** с описанием: что, зачем, как проверяли.

---

## Стиль кода

### Python

- PEP 8, type hints где это помогает читать, docstrings для публичных функций.
- Используйте `ruff` и `black` для форматирования:

  ```bash
  ruff check .
  black --check .
  ```

### React / TypeScript

- Функциональные компоненты, hooks, имена на английском.
- Форматирование через Prettier (если настроен в `web/frontend`).

### Коммиты

- Конвенциональные, на русском или английском, коротко и по делу.
- Примеры:

  ```text
  docs: обновил README
  feat: добавил узел action.slack
  fix: починил fallback при отсутствии Redis
  security: закрыл path traversal в file_tools
  test: добавил тест на workspace isolation
  ```

### Язык

- Пользовательский текст — на русском.
- Код и комментарии — на английском.

---

## Что точно не надо коммитить

- `.env`, `.agent_secret`, токены, ключи, пароли.
- `node_modules/`, `__pycache__/`, `.venv/`, build-артефакты.
- Большие бинарные файлы без согласования.

---

## DoD для PR

- [ ] Релевантные тесты проходят.
- [ ] `scripts/check-secrets.sh` не находит секретов.
- [ ] Изменение соответствует вайбу продукта: professional, calm B2B, outcome-first.
- [ ] README/AGENTS/Docs обновлены, если меняется контракт или запуск.
- [ ] Минимальный diff: не затронут соседний код без необходимости.

---

## Шаблон PR

```markdown
## Что
Краткое описание изменения.

## Зачем
Какую боль решает или какую фичу добавляет.

## Как проверял
- Команды/тесты, которые запускал.
- Результаты.

## Риски
Что могло сломаться и почему это безопасно.
```

---

## Вопросы?

Откройте issue или напишите в обсуждениях. Для AI-агентов — см. [AGENTS.md](./AGENTS.md).
