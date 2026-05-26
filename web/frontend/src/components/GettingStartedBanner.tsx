import { Link } from 'react-router-dom';
import { t } from '../i18n';

interface GettingStartedBannerProps {
  onOpenDemo?: () => void;
}

/** First-run guidance when workspace has no workflows yet. */
export default function GettingStartedBanner({ onOpenDemo }: GettingStartedBannerProps) {
  return (
    <section
      className="card getting-started-banner"
      style={{
        marginBottom: 24,
        padding: 20,
        borderColor: 'var(--accent)',
        background: 'linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%)',
      }}
    >
      <h2 style={{ fontSize: 16, margin: '0 0 8px' }}>{t('dashboard.gettingStartedTitle')}</h2>
      <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '0 0 16px' }}>{t('dashboard.gettingStartedDesc')}</p>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <Link to="/marketplace" className="btn btn-primary">{t('dashboard.gettingStartedMarketplace')}</Link>
        {onOpenDemo ? (
          <button type="button" className="btn" onClick={onOpenDemo}>{t('dashboard.tryDemoModal')}</button>
        ) : (
          <Link to="/showcase#playground" className="btn">{t('dashboard.tryDemo')}</Link>
        )}
        <Link to="/workflows" className="btn btn-ghost">{t('nav.workflows')}</Link>
      </div>
    </section>
  );
}
