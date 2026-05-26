import type { FeatureStatus } from '../components/ui/FeatureTag';

/** Showcase vertical id → marketplace template for «Установить похожий». */
export const SHOWCASE_CARD_TEMPLATES: Record<string, string> = {
  ararat: 'tpl_beauty_consultant',
  pegasszn: 'tpl_content_repurpose',
  pretenzia: 'tpl_lead_qualifier',
  'my-agent': 'tpl_competitor_intelligence',
  podolog: 'tpl_content_repurpose',
  docbrain: 'tpl_lead_qualifier',
  kormoved: 'tpl_competitor_intelligence',
};

/** UI maturity tag for a showcase card (not the JSON `status: live` field). */
export function showcaseCardFeatureStatus(card: {
  id: string;
  cta_url: string | null;
}): FeatureStatus {
  if (card.id === 'my-agent') return 'live';
  if (card.cta_url) return 'beta';
  if (SHOWCASE_CARD_TEMPLATES[card.id]) return 'beta';
  return 'mock';
}
