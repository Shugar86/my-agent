# My Agent — 90-Day Roadmap (Workflow + UX/UI + Marketplace)

**Стратегическая цель:** Превратить My Agent из мощного технического фреймворка в продукт для бизнеса, который конкурирует с ASCN.ai по простоте запуска и при этом сохраняет техническое превосходство.

**Ключевой дифференциатор:** "Мощь My Agent + простота ASCN + безопасность Docker sandbox"

---

## Phase 1: Workflow Core + Базовый UI (Дни 1–30)

**Цель:** Дать пользователям возможность строить автономные связки без кода.

### Ключевые фичи
- **Workflow Engine v1** (n8n-подобный)
  - Ноды: Trigger (webhook, schedule, email, new lead), Agent/Skill, Condition, Action (email, telegram, sheets, webhook)
  - Простой JSON-based executor + визуальный редактор (React Flow / LiteGraph)
  - Сохранение workflow в БД + запуск по расписанию
- **5 ключевых интеграций**
  - Telegram (send/receive)
  - Gmail (read + send)
  - Google Sheets (read/write)
  - Slack (notifications)
  - Notion (create page / update DB)
- **Marketplace MVP**
  - 10–15 готовых workflow-шаблонов
  - Кнопка "Install → Clone to my workspace"

### UX/UI задачи
- Новый Dashboard с карточками "Запусти за 1 клик"
- Workflow Builder (первый черновик) — drag-and-drop
- Onboarding Wizard (3 шага)

### Метрики успеха
- Пользователь может создать и запустить workflow за < 8 минут
- Время от "зашёл на сайт" до первого результата ≤ 10 минут

---

## Phase 2: Marketplace + UX/UI Overhaul (Дни 31–60)

**Цель:** Сделать продукт красивым и продающим.

### Ключевые фичи
- Полноценный Marketplace (25+ шаблонов, рейтинги, публикация)
- Agent Builder 2.0 (визуальный конструктор агентов)
- Event-driven Triggers + память между запусками

### UX/UI задачи (основной фокус)
- Полный редизайн Web UI (тёмная тема, sidebar, метрики)
- Production-ready Workflow Canvas (zoom, mini-map, execution timeline)
- Chat 2.0 + лендинг / marketing site

### Метрики успеха
- Marketplace имеет ≥ 25 шаблонов
- Среднее время создания workflow ≤ 5 минут
- NPS ≥ 40

---

## Phase 3: Business Features + Go-to-Market (Дни 61–90)

**Цель:** Подготовить продукт к монетизации и масштабу.

### Ключевые фичи
- 20+ готовых бизнес-сценариев
- Observability & Logs (cost tracking, alerts)
- Multi-user + Roles + Team workspaces
- SaaS preparation (Stripe, usage-based pricing)

### UX/UI задачи
- Logs & Analytics Dashboard
- Красивый onboarding подключения сервисов
- Performance & Polish (skeleton loaders, анимации)

### Метрики успеха
- Пользователь запускает production workflow за < 5 минут с нуля
- Готовы pricing tiers и onboarding flow

---

## Приоритетная последовательность

1. Workflow Engine core
2. Telegram + Gmail + Sheets интеграции
3. Dashboard + Workflow Builder UI
4. Marketplace MVP
5. Onboarding Wizard
6. Полный редизайн + лендинг

**Trade-off:** В Phase 1 делаем упрощённый визуальный редактор, чтобы быстрее выйти на рынок. Идеальный canvas — в Phase 2.

---

**Итог к концу 90 дней:**
- Продукт, который реально конкурирует с ASCN
- Marketplace + workflow engine как growth-драйверы
- Современный UX/UI, готовый к инвесторам и клиентам

---

*Сохранено: 2026-05-25*