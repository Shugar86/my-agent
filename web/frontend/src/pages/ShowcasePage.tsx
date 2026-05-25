import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import DemoModal from '../components/DemoModal';
import PageHeader from '../components/ui/PageHeader';
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

/** Authenticated mirror of /showcase — cards from JSON, featured templates from API. */
export default function ShowcasePage() {
  const [data, setData] = useState<ShowcaseData | null>(null);
  const [featuredTemplates, setFeaturedTemplates] = useState<ShowcaseData['featured_templates']>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [demoOpen, setDemoOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch('/welcome-assets/data/showcase.json')
        .then((r) => {
          if (!r.ok) throw new Error('Failed to load showcase');
          return r.json();
        }),
      fetch('/api/public/templates?featured=true&limit=9')
        .then((r) => (r.ok ? r.json() : { templates: [] }))
        .catch(() => ({ templates: [] })),
    ])
      .then(([showcaseJson, featuredJson]) => {
        setData(showcaseJson);
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
          apiTemplates.length > 0 ? apiTemplates : showcaseJson.featured_templates || [],
        );
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="page-content">
        <PageHeader title={t('showcase.title')} subtitle={error} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page-content">
        <PageHeader title={t('showcase.title')} subtitle={t('common.loading')} />
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
          <>
            <button type="button" className="btn btn-primary" onClick={() => setDemoOpen(true)}>
              {t('onboarding.runDemo')}
            </button>
            <a href="/showcase" className="btn btn-secondary" target="_blank" rel="noopener noreferrer">
              {t('showcase.publicPage')} ↗
            </a>
          </>
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
              <span className="badge badge-featured">
                {card.status === 'live' ? t('showcase.liveBadge') : t('showcase.labBadge')}
              </span>
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
              <button type="button" className="btn btn-primary" style={{ width: '100%' }} onClick={() => setDemoOpen(true)}>
                {card.cta_label}
              </button>
            ) : (
              <span className="btn btn-secondary" style={{ width: '100%', opacity: 0.7 }}>{card.cta_label}</span>
            )}
          </article>
        ))}
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
          <div key={tpl.id} className="card" style={{ padding: 16 }}>
            <div style={{ fontSize: 11, color: 'var(--accent)', textTransform: 'uppercase', marginBottom: 4 }}>{tpl.category}</div>
            <h3 style={{ fontSize: 14, marginBottom: 6 }}>{tpl.name}</h3>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{tpl.description}</p>
          </div>
        ))}
      </div>
      <Link to="/marketplace" className="btn btn-primary">
        {t('common.viewAll')}
      </Link>

      <DemoModal open={demoOpen} onClose={() => setDemoOpen(false)} />
    </div>
  );
}
