# Legacy static website (deprecated)

Статический лендинг в `website/` **не используется** для основного UI с v4.0.0.

Актуальный интерфейс:

| Маршрут | Реализация |
|---------|------------|
| `/`, `/demo`, `/showcase` | React SPA (`web/frontend/` → `web/static/app/`) |
| `/login` | React или `web/static/login.html` |
| `/app/*` | React SPA |

Папка `website/` сохранена для:

- маркетинговых ассетов (иконки, OG-image) — часть отдаётся через `/welcome-assets`
- [BRAND.md](./BRAND.md) — positioning и tone

Не редактируйте `website/index.html` для продуктовых изменений — правки в `web/frontend/src/`.
