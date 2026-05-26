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

/** Feature maturity for page sections and actions. */
export const PAGE_FEATURE_STATUS: Record<string, FeatureStatus> = {
  'marketplace.demoRun': 'mock',
  'showcase.cards': 'mock',
  'showcase.playground': 'live',
  'dashboard.caseCards': 'mock',
  'settings.billing.stripe': 'coming-soon',
  'chat.stream': 'beta',
  'playground.offline': 'mock',
  'publicTemplate.preview': 'mock',
};
