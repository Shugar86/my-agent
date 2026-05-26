import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import FeatureTag from '../ui/FeatureTag';
import { listTemplates } from '../../api/appClient';
import { loginUrl } from '../../lib/routes';
import { t } from '../../i18n';

interface TemplateItem {
  id: string;
  name: string;
  description: string;
  category: string;
}

const FALLBACK_TEMPLATES: TemplateItem[] = [
  { id: 'tpl_competitor_intelligence', name: 'Competitor Intelligence', category: 'Research', description: 'Multi-agent competitive brief with SWOT and DOCX output.' },
  { id: 'tpl_beauty_consultant', name: 'Beauty Salon Consultant', category: 'Sales', description: 'Telegram AI consultant with catalog and appointment booking.' },
  { id: 'tpl_lead_qualifier', name: 'Lead Qualifier', category: 'Sales', description: 'Qualify inbound leads and route to CRM or human.' },
  { id: 'tpl_content_repurpose', name: 'Content Repurpose', category: 'Marketing', description: 'Turn one source into posts for Telegram, VK and email.' },
];

interface TemplateCardGridProps {
  limit?: number;
  publicMode?: boolean;
  onInstall?: (id: string) => void;
  installingId?: string | null;
}

/** Shared template card grid for landing and marketplace previews. */
export default function TemplateCardGrid({
  limit = 4,
  publicMode = false,
  onInstall,
  installingId = null,
}: TemplateCardGridProps) {
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listTemplates(undefined, 'popular')
      .then((list) => {
        const arr = Array.isArray(list) ? list : [];
        setTemplates(
          arr.slice(0, limit).map((tpl) => ({
            id: tpl.id,
            name: tpl.name,
            description: tpl.description,
            category: tpl.category,
          })),
        );
      })
      .catch(() => setTemplates(FALLBACK_TEMPLATES.slice(0, limit)))
      .finally(() => setLoading(false));
  }, [limit]);

  if (loading) {
    return (
      <div className="landing-cards-grid">
        {Array.from({ length: limit }, (_, i) => (
          <div key={i} className="skeleton" style={{ height: 160 }} />
        ))}
      </div>
    );
  }

  const items = templates.length > 0 ? templates : FALLBACK_TEMPLATES.slice(0, limit);

  return (
    <div className="landing-cards-grid">
      {items.map((tpl) => (
        <article key={tpl.id} className="landing-card">
          <div style={{ fontSize: 11, color: 'var(--landing-accent)', textTransform: 'uppercase', marginBottom: 6 }}>
            {tpl.category}
          </div>
          <h3>{tpl.name}</h3>
          <p style={{ marginBottom: 16 }}>{tpl.description}</p>
          {publicMode ? (
            <a href={loginUrl(`/app/marketplace`)} className="landing-btn landing-btn-secondary" style={{ width: '100%' }}>
              {t('showcase.installTemplate')}
            </a>
          ) : onInstall ? (
            <button
              type="button"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={installingId === tpl.id}
              onClick={() => onInstall(tpl.id)}
            >
              {installingId === tpl.id ? t('common.loading') : t('showcase.installTemplate')}
            </button>
          ) : (
            <Link to="/app/marketplace" className="landing-btn landing-btn-secondary" style={{ width: '100%' }}>
              {t('common.viewAll')}
            </Link>
          )}
          {!publicMode && (
            <FeatureTag status="mock" label={t('featureTag.preview')} showDot={false} className="marketplace-demo-tag" />
          )}
        </article>
      ))}
    </div>
  );
}
