# COCKPIT — my-agent

## Who this project is (personality)

**Прагматичный AI-оператор для бизнеса**, не «ещё один чат-бот». Говорит языком результата (оператор, workflow, артефакт), держит спокойный B2B-тон и при этом показывает магию за секунды на лендинге — без регистрации и без обещаний, которые backend не подтверждает.

## How it feels (tone, vibe по слоям)

| Слой / persona | Vibe | Тон |
|----------------|------|-----|
| **Лендинг** (`/`, `/showcase`) | `energetic` + `honest` | Короткий hero, live preview, showcase как социальное доказательство; badges честные (Live/Beta/Preview) |
| **Public demo** | `curious` | «Опишите задачу» → персона за ~10 с; fallback/mock без стыда, не красный экран |
| **Продукт** (`/app/*`) | `professional` + `calm` | Chat-first dashboard, тёмная product-тема, фокус на работе, не на каталоге технологий |
| **Инвестор / питч** | `confident` | 3-минутный скрипт, 7 vertical cases, метрики marketplace и live deployments |
| **CLI / разработчик** | `direct` | Rich-вывод, явные команды, pytest gate — без магии |

Общий вайб продукта по VibeCraft: **`calm` B2B с вспышкой `energetic` на входе** (funnel), outcome-first.

## For whom (3 аудитории)

1. **Владелец бизнеса / операционный менеджер** — нужен AI-оператор под задачу без разработчика и интегратора.
2. **Инвестор / партнёр** — нужен быстрый live demo, 7 production-кейсов, понятная экономика time-to-wow.
3. **Инженер / power user** — нужны workflow DAG, skills, CLI, Docker one-command, расширяемость через registry и plugins.

## Emotions it evokes

- **Облегчение** — «можно описать словами, не кодом»
- **Доверие** (при green gate) — аудиты закрыты, честные статусы
- **Любопытство** — live preview на первом экране
- **Контроль** — dashboard, workflows, marketplace шаблонов
- **Осторожность** [если ключей нет] — mock/fallback вместо пустых обещаний

## What makes it special (уникальные черты)

1. **Agent OS, не чат** — AutoAgentFactory, orchestrator, 10 типовых агентов + 30+ skills.
2. **Funnel без трения** — public agent-preview до login; продукт после JWT/OAuth.
3. **7 live deployments** — Mary Jewelry, PEGAS, DocBrain, Pretenzia и др. как proof, не слайды.
4. **Workflow + marketplace** — visual DAG (21+ узлов) и 50+ шаблонов install-in-one-click.
5. **Инженерная дисциплина** — TROUBLES gate, security remediation, Prometheus, production PG/Redis.

## Current focus

Сейчас проект **закрепляет v4 pivot**: OpenRouter и LLM fallback стабилизируют demo; порт 8020 открыт для внешнего доступа; entrypoint не валит контейнер на seed. Следующий эмоциональный рубеж — **довести Phase 1 до prod**: чтобы лендинг и agent-preview на VDS ощущались так же живо, как локально, и чтобы reload чата в `/app/chat` не ронял доверие. Блокеры и конкретные шаги — в [STATE.md](STATE.md).
