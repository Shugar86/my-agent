import type { FeatureStatus } from '../components/ui/FeatureTag';

/** Feature maturity status per nav route (full paths). */
export const NAV_FEATURE_STATUS: Record<string, FeatureStatus> = {
  '/app': 'live',
  '/app/workflows': 'live',
  '/app/marketplace': 'live',
  '/app/chat': 'beta',
  '/app/analytics': 'beta',
  '/app/settings': 'live',
  '/app/showcase': 'live',
  '/app/demo': 'live',
  '/app/agents': 'live',
  '/app/knowledge': 'beta',
  '/app/mcp': 'beta',
  '/app/admin': 'live',
};

/** Public marketing routes (no sidebar). */
export const PUBLIC_ROUTE_STATUS: Record<string, FeatureStatus> = {
  '/': 'live',
  '/showcase': 'live',
  '/demo': 'live',
};

/** Feature maturity for page sections and actions. */
export const PAGE_FEATURE_STATUS: Record<string, FeatureStatus> = {
  'marketplace.demoRun': 'mock',
  'showcase.cards': 'mock',
  'showcase.playground': 'live',
  'showcase.marketplace': 'mock',
  'dashboard.caseCards': 'mock',
  'landing.heroStats': 'mock',
  'landing.liveDemo': 'live',
  'settings.billing.stripe': 'coming-soon',
  'chat.stream': 'beta',
  'playground.offline': 'mock',
  'publicTemplate.preview': 'mock',
  'onboarding.integrations': 'beta',
  'onboarding.workspace': 'live',
};

/** Resolve page section status with live fallback. */
export function getPageFeatureStatus(key: string): FeatureStatus {
  return PAGE_FEATURE_STATUS[key] ?? 'live';
}

/** Resolve public route status. */
export function getPublicRouteStatus(path: string): FeatureStatus {
  return PUBLIC_ROUTE_STATUS[path] ?? 'live';
}
