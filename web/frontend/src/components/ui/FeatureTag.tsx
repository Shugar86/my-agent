import { t } from '../../i18n';

export type FeatureStatus = 'live' | 'beta' | 'mock' | 'coming-soon' | 'broken';

const LABEL_KEYS: Record<FeatureStatus, 'featureTag.live' | 'featureTag.beta' | 'featureTag.preview' | 'featureTag.comingSoon' | 'featureTag.broken'> = {
  live: 'featureTag.live',
  beta: 'featureTag.beta',
  mock: 'featureTag.preview',
  'coming-soon': 'featureTag.comingSoon',
  broken: 'featureTag.broken',
};

interface FeatureTagProps {
  status: FeatureStatus;
  label?: string;
  reason?: string;
  showDot?: boolean;
  className?: string;
}

/** Visual status badge for Live / Beta / Preview / Coming soon features. */
export default function FeatureTag({
  status,
  label,
  reason,
  showDot,
  className = '',
}: FeatureTagProps) {
  if (status === 'broken' && !import.meta.env.DEV) return null;

  const resolvedLabel = label ?? t(LABEL_KEYS[status]);
  const useDot = showDot ?? status === 'live';
  const title = reason ?? resolvedLabel;

  return (
    <span
      className={`feature-tag feature-tag--${status} ${className}`.trim()}
      title={title}
    >
      {useDot && status === 'live' && <span className="feature-tag__dot" aria-hidden />}
      {resolvedLabel}
    </span>
  );
}
