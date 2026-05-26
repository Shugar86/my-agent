# Deprecated static marketing pages

HTML pages in this folder (`index.html`, `demo.html`, `showcase.html`) are **deprecated** as of v3.5.

Public routes are now served by the React SPA:

| Legacy URL | React route |
|------------|-------------|
| `/` | `LandingPage` |
| `/demo` | `PublicDemoPage` |
| `/showcase` | `PublicShowcasePage` |

**Keep:** `data/showcase.json`, `assets/`, CSS used by `/welcome-assets` mount.

**Do not edit** HTML pages for copy changes — update `web/frontend/src/i18n/ru.ts` (`landing.*`) instead.
