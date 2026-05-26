import type { FeatureStatus } from '../components/ui/FeatureTag';

/** Feature maturity status per nav route (basename-relative paths). */
export const NAV_FEATURE_STATUS: Record<string, FeatureStatus> = {
  '/': 'live',
  '/workflows': 'live',
  '/marketplace': 'live',
  '/chat': 'beta',
  '/analytics': 'beta',
  '/settings': 'live',
  '/showcase': 'live',
  '/demo': 'live',
  '/agents': 'live',
  '/knowledge': 'beta',
  '/mcp': 'beta',
  '/admin': 'live',
};
