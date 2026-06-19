# Deprecated static website

Маркетинговый сайт перенесён в React SPA (`web/frontend/` → `web/static/app/`).

Каталог `website/` сохранён только для legacy-ассетов (`style.css`, `login.css`, SVG) и ссылок из старых деплоев.

**Актуальные маршруты:**

| URL | Назначение |
|-----|------------|
| `/` | Лендинг + Agent Preview |
| `/showcase` | 7 vertical кейсов |
| `/demo` | Shortcut на agent preview |
| `/login` | JWT + Google OAuth |
| `/app/*` | Продукт |

Не редактируйте `website/*.html` для новых фич — только `web/frontend/`.
