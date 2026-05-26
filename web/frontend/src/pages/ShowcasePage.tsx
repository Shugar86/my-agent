import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { installTemplate } from '../api/appClient';
import PlaygroundDemo from '../components/demo/PlaygroundDemo';
import FeatureTag from '../components/ui/FeatureTag';
import PageHeader from '../components/ui/PageHeader';
import { useToast } from '../components/ui/Toast';
import { OFFLINE_SHOWCASE, fetchWithDemoFallback } from '../lib/demoFallback';
import { t } from '../i18n';

interface PersonaSnippet {
  type?: string;
  text: string;
}

interface ShowcaseCard {
  id: string;
  vertical: string;
  title: string;
  one_liner: string;
  status: 'live' | 'lab';
  platform: string;
  llm: string;
  metric: string;
  icon: string;
  cta_label: string;
  cta_url: string | null;
  persona: {
    role: string;
    voice: string;
    snippets: PersonaSnippet[];
  };
}

interface ShowcaseData {
  meta: { live_deployments: number; personas: number; templates: number };
  cards: ShowcaseCard[];
  featured_templates: Array<{
    id: string;
    name: string;
    category: string;
    description: string;
    nodes: number;
  }>;
}

/** Authenticated showcase — vertical cases, playground, featured templates. */
export default function ShowcasePage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [data, setData] = useState<ShowcaseData | null>(null);
  const [featuredTemplates, setFeaturedTemplates] = useState<ShowcaseData['featured_templates']>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [dataSource, setDataSource] = useState<'live' | 'mock'>('live');
  const [installingId, setInstallingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchWithDemoFallback<ShowcaseData>('/welcome-assets/data/showcase.json', OFFLINE_SHOWCASE),
      fetch('/api/public/templates?featured=true&limit=9')
        .then((r) => (r.ok ? r.json() : { templates: [] }))
        .catch(() => ({ templates: [] })),
    ])
      .then(([showcaseResult, featuredJson]) => {
        setData(showcaseResult.data);
        setDataSource(showcaseResult.source);
        if (showcaseResult.source === 'mock') showToast(t('featureTag.previewData'), 'info');
        const apiTemplates = (featuredJson.templates || []).map(
          (tpl: { id: string; name: string; category: string; description: string; nodes?: number }) => ({
            id: tpl.id,
            name: tpl.name,
            category: tpl.category,
            description: tpl.description,
            nodes: tpl.nodes || 0,
          }),
        );
        setFeaturedTemplates(
          apiTemplates.length > 0 ? apiTemplates : showcaseResult.data.featured_templates || [],
        );
      })
      .catch(() => setError(t('showcase.loadError')))
      .finally(() => setLoading(false));
  }, [showToast]);

  const handleInstall = async (templateId: string) => {
    setInstallingId(templateId);
    try {
      const result = await installTemplate(templateId);
      navigate(`/workflows/${result.workflow.id}`);
    } catch {
      showToast(t('dashboard.installFailed'), 'error');
    } finally {
      setInstallingId(null);
    }
  };

  if (loading) {
    return (
      <div className="page-content">
        <PageHeader title={t('showcase.title')} subtitle={t('common.loading')} />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: 16,
            marginBottom: 32,
          }}
        >
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="skeleton" style={{ height: 220 }} />
          ))}
        </div>
        <div className="skeleton" style={{ height: 280 }} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-content">
        <PageHeader title={t('showcase.title')} subtitle={error || t('showcase.loadError')} />
        <PlaygroundDemo />
      </div>
    );
  }

  const meta = data.meta;

  return (
    <div className="page-content">
      <PageHeader
        title={t('showcase.title')}
        subtitle={t('showcase.subtitle', {
          live: meta.live_deployments,
          personas: meta.personas,
          templates: meta.templates,
        })}
        actions={
          dataSource === 'mock' ? <FeatureTag status="mock" label={t('featureTag.previewData')} /> : undefined
        }
      />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 16,
          marginBottom: 32,
        }}
      >
        {data.cards.map((card) => (
          <article
            key={card.id}
            className="card"
            style={{
              padding: 20,
              borderStyle: card.status === 'lab' ? 'dashed' : 'solid',
            }}
          >
            <div style={{ display: 'flex', gap: 12, marginBottom: 10 }}>
              <img
                src={`/welcome-assets/assets/icons/${card.icon}.svg`}
                alt=""
                width={40}
                height={40}
              />
              <div>
                <div style={{ fontSize: 11, color: 'var(--accent-secondary)', fontWeight: 600, textTransform: 'uppercase' }}>
                  {card.vertical}
                </div>
                <h3 style={{ fontSize: 16, margin: '4px 0 0' }}>{card.title}</h3>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
              <FeatureTag status={card.status === 'live' ? 'live' : 'beta'} />
              <span className="badge">{card.platform}</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>{card.one_liner}</p>
            <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>{card.metric}</p>
            <button
              type="button"
              className="btn btn-ghost"
              style={{ fontSize: 12, padding: '4px 8px', marginBottom: 12 }}
              onClick={() => setExpanded(expanded === card.id ? null : card.id)}
            >
              {expanded === card.id ? t('showcase.personaHide') : t('showcase.personaToggle')}
            </button>
            {expanded === card.id && (
              <div style={{ fontSize: 12, background: 'var(--bg-tertiary)', borderRadius: 8, padding: 12, marginBottom: 12 }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{card.persona.role}</div>
                <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', marginBottom: 8 }}>{card.persona.voice}</div>
                {card.persona.snippets.map((s, i) => (
                  <div key={i} style={{ marginBottom: 6, paddingLeft: 8, borderLeft: '2px solid var(--accent)' }}>
                    {s.text}
                  </div>
                ))}
              </div>
            )}
            {card.cta_url ? (
              <a href={card.cta_url} className="btn btn-secondary" target="_blank" rel="noopener noreferrer" style={{ width: '100%' }}>
                {card.cta_label}
              </a>
            ) : card.id === 'my-agent' ? (
              <a href="#playground" className="btn btn-primary" style={{ width: '100%', display: 'block', textAlign: 'center' }}>
                {card.cta_label}
              </a>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <FeatureTag status="coming-soon" />
                <button type="button" className="btn btn-secondary" style={{ width: '100%' }} disabled title={t('showcase.comingSoonHint')}>
                  {card.cta_label}
                </button>
              </div>
            )}
          </article>
        ))}
      </div>

      <div id="playground">
        <PlaygroundDemo />
      </div>

      <h2 style={{ fontSize: 18, marginBottom: 12 }}>{t('showcase.featuredTemplates')}</h2>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 12,
          marginBottom: 16,
        }}
      >
        {featuredTemplates.map((tpl) => (
          <div key={tpl.id} className="card" style={{ padding: 16, display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: 11, color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 4 }}>{tpl.category}</div>
            <h3 style={{ fontSize: 14, marginBottom: 6 }}>{tpl.name}</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', flex: 1, marginBottom: 12 }}>{tpl.description}</p>
            <button
              type="button"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={installingId === tpl.id}
              onClick={() => handleInstall(tpl.id)}
            >
              {installingId === tpl.id ? t('common.loading') : t('showcase.installTemplate')}
            </button>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <Link to="/marketplace" className="btn btn-primary">
          {t('common.viewAll')}
        </Link>
        <a href="/showcase" className="btn btn-ghost" target="_blank" rel="noopener noreferrer" style={{ fontSize: 13 }}>
          {t('showcase.publicVersion')}
        </a>
      </div>
    </div>
  );
}
