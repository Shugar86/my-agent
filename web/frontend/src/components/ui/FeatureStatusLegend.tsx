import FeatureTag from './FeatureTag';
import { t } from '../../i18n';

/** Compact legend explaining Live / Beta / Preview / Coming soon badges. */
export default function FeatureStatusLegend() {
  return (
    <div
      className="feature-status-legend"
      title={t('featureTag.legendTitle')}
      style={{
        padding: '10px 18px',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '6px 10px',
        alignItems: 'center',
      }}
    >
      <span style={{ fontSize: 10, color: 'var(--text-muted)', width: '100%', marginBottom: 2 }}>
        {t('featureTag.legendTitle')}
      </span>
      <span style={{ fontSize: 10, color: 'var(--text-subtle)', width: '100%', marginBottom: 4 }}>
        {t('featureTag.legendDesc')}
      </span>
      <FeatureTag status="live" showDot />
      <FeatureTag status="beta" showDot={false} />
      <FeatureTag status="mock" showDot={false} />
      <FeatureTag status="coming-soon" showDot={false} />
    </div>
  );
}
