# Legacy static website (deprecated)

Статические HTML-страницы в `website/` (`index.html`, `demo.html`, `showcase.html`) **не используются** для основного UI.

Актуальный маркетинговый слой — React SPA:

- `/` — лендинг с AgentPreviewWidget
- `/showcase` — 7 vertical кейсов
- `/demo` — shortcut на agent preview

CSS из `website/` может подключаться как `/welcome-assets` для legacy-совместимости. Новые изменения — только в `web/frontend/`.

См. [BRAND.md](./BRAND.md) и [docs/README.md](../docs/README.md).
