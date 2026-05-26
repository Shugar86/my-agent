# My Agent — Design System

Design tokens and component classes for the React SPA at `/app/*`.

**Source of truth:** `src/layout/theme.css`

## Visual identity

- **Aesthetic:** GitHub-dark inspired, professional B2B
- **Default theme:** Dark; light via `[data-theme="light"]` + `localStorage.my-agent.theme`
- **Font:** Inter, system-ui fallback
- **Primary CTA:** Green `#238636` (`.btn-primary`)
- **Accent:** Blue `#58a6ff` (links, stats, active nav)

## Color tokens (dark)

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#0d1117` | Page background |
| `--bg-secondary` | `#161b22` | Sidebar, cards |
| `--bg-tertiary` | `#21262d` | Hover, user messages |
| `--accent` | `#58a6ff` | Links, highlights |
| `--success` | `#238636` | Primary buttons |
| `--danger` | `#f85149` | Errors |
| `--warning` | `#d29922` | Logic nodes |

## Layout

- Sidebar: 240px (overlay drawer ≤768px)
- Radii: 4px / 6px / 10px
- Spacing: page padding 30px; card padding 16px

## Component classes

- **Buttons:** `.btn`, `.btn-primary`, `.btn-danger`, `.btn-ghost`
- **Forms:** `.input`, `textarea.input`
- **Surfaces:** `.card`, `.badge`, `.badge-featured`
- **Status:** `.feature-tag`, `.feature-tag--live|beta|mock|coming-soon|broken` — React: `<FeatureTag />`
- **Feedback:** `.skeleton`, `.toast`, `.empty-state`
- **Layout:** `.page-header`, `.page-content`, `.modal-*`, `.breadcrumbs`
- **Demo:** `.demo-stepper`, `.playground-demo`, `.playground-presets`
- **Chat:** `.chat-bubble`, `.chat-tool-call`, `.chat-markdown`
- **Workflow:** `.node-running` (pulse glow)

## Feature status tags

| Status | Meaning | Use |
|--------|---------|-----|
| `live` | Connected to backend | Nav core items, successful demo runs |
| `beta` | Works but unstable | Chat, Analytics, MCP |
| `mock` | Prerecorded / static data | Demo runs without API keys |
| `coming-soon` | UI only | Dead showcase CTAs, Stripe billing |

Registry: `src/config/featureRegistry.ts` (`NAV_FEATURE_STATUS`).

## i18n

Russian strings in `src/i18n/ru.ts`, accessed via `t('nav.dashboard')`.

## Do not use

Root `DESIGN-opencode-reference.md` is an OpenCode marketing reference — not this product.
