/** Authenticated SPA base path (no trailing slash except for dashboard root). */
export const APP_BASE = '/app';

/** Build an in-app route under `/app`. */
export function appRoute(path = ''): string {
  if (!path || path === '/') return APP_BASE;
  return `${APP_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}

/** Login URL with optional post-auth redirect. */
export function loginUrl(next = `${APP_BASE}/onboarding`): string {
  return `/login?next=${encodeURIComponent(next)}`;
}
