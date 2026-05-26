import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listAgents, listTemplates, installTemplate } from '../api/appClient';
import { listWorkflows } from '../api/workflowClient';
import type { Workflow } from '../types/workflow';
import DemoModal from '../components/DemoModal';
import GettingStartedBanner from '../components/GettingStartedBanner';
import FeatureTag from '../components/ui/FeatureTag';
import PageHeader from '../components/ui/PageHeader';
import { useToast } from '../components/ui/Toast';
import { fetchWithDemoFallback } from '../lib/demoFallback';
import { t } from '../i18n';

interface ShowcaseCard {
  id: string;
  vertical: string;
  title: string;
  one_liner: string;
  status: 'live' | 'lab';
  platform: string;
  metric: string;
  icon: string;
  persona: {
    snippets: Array<{ text: string }>;
  };
}

interface DashboardStats {
  workflows: number;
  templates: number;
  integrations: number;
  agents: number;
}

/** Home dashboard: showcase-first, stats, quick start templates and recent workflows. */
export default function Dashboard() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState<Array<{ id: string; name: string; description: string; category: string; tags?: string[] }>>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [showcaseCards, setShowcaseCards] = useState<ShowcaseCard[]>([]);
  const [stats, setStats] = useState<DashboardStats>({ workflows: 0, templates: 0, integrations: 0, agents: 0 });
  const [demoOpen, setDemoOpen] = useState(false);
  const [showcaseSource, setShowcaseSource] = useState<'live' | 'mock'>('live');

  useEffect(() => {
    Promise.all([
      fetchWithDemoFallback<{ cards: ShowcaseCard[] }>()
        .then(({ data, source }) => {
          setShowcaseSource(source);
          return data;
        }),
      listTemplates(undefined, 'popular').catch(() => []),
      listWorkflows().catch(() => []),
      listAgents().catch(() => []),
      fetch('/api/integrations').then((r) => (r.ok ? r.json() : [])).catch(() => []),
    ]).then(([showcaseData, tplList, wfList, agentList, integrations]) => {
      const cards = (showcaseData.cards || []) as ShowcaseCard[];
      const featuredIds = ['ararat', 'pegasszn', 'pretenzia'];
      const liveFeatured = cards.filter(
        (c) => c.status === 'live' && featuredIds.includes(c.id),
      );
      setShowcaseCards(liveFeatured.length > 0 ? liveFeatured : cards.filter((c) => c.status === 'live').slice(0, 3));
      const tplArray = Array.isArray(tplList) ? tplList : [];
      setTemplates(tplArray.slice(0, 4));
      const wfArray = Array.isArray(wfList) ? wfList : [];
      setWorkflows(wfArray.slice(0, 5));
      const integrationList = Array.isArray(integrations) ? integrations : integrations?.integrations || [];
      const connected = integrationList.filter((i: { configured?: boolean }) => i.configured).length;
      setStats({
        workflows: wfArray.length,
        templates: tplArray.length,
        integrations: connected,
        agents: Array.isArray(agentList) ? agentList.length : 0,
      });
      setLoading(false);
    });
  }, []);

  const handleInstall = async (id: string) => {
    try {
      const result = await installTemplate(id);
      navigate(`/workflows/${result.workflow.id}`);
    } catch {
      showToast(t('dashboard.installFailed'), 'error');
    }
  };

  if (loading) {
    return (
      <div className="page-content">
        <div className="skeleton" style={{ height: 120, marginBottom: 24 }} />
        <div className="cards-grid">
          {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 160 }} />)}
        </div>
      </div>
    );
  }

  const statCards = [
    { label: t('dashboard.activeWorkflows'), value: stats.workflows, hint: t('dashboard.total') },
    { label: t('dashboard.templates'), value: stats.templates, hint: t('dashboard.inMarketplace') },
    { label: t('dashboard.integrations'), value: stats.integrations, hint: t('dashboard.connected') },
    { label: t('dashboard.agents'), value: stats.agents, hint: t('dashboard.available') },
  ];

  return (
    <div className="page-content">
      <DemoModal open={demoOpen} onClose={() => setDemoOpen(false)} />

      <section className="dashboard-hero">
        <div style={{ flex: '1 1 320px' }}>
          <div className="dashboard-hero__badge">{t('dashboard.heroBadge')}</div>
          {showcaseSource === 'mock' && (
            <div style={{ marginBottom: 8 }}>
              <FeatureTag status="mock" label={t('featureTag.previewData')} />
            </div>
          )}
          <h1 className="dashboard-hero__title">{t('dashboard.heroTitle')}</h1>
          <p className="dashboard-hero__desc">{t('dashboard.heroDesc')}</p>
        </div>
        <div className="dashboard-hero__actions">
          <Link to="/marketplace" className="btn btn-primary">{t('dashboard.heroPrimaryCta')}</Link>
          <button type="button" className="btn" onClick={() => setDemoOpen(true)}>
            {t('dashboard.tryDemoModal')}
          </button>
        </div>
      </section>

      {stats.workflows === 0 && (
        <GettingStartedBanner onOpenDemo={() => setDemoOpen(true)} />
      )}

      <section style={{ marginBottom: 32 }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: 12,
          }}
        >
          {statCards.map((card) => (
            <div key={card.label} className="card" style={{ padding: 16 }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{card.label}</div>
              <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--accent)' }}>{card.value}</div>
              <div style={{ fontSize: 11, color: 'var(--text-subtle)' }}>{card.hint}</div>
            </div>
          ))}
        </div>
      </section>

      <section style={{ marginBottom: 32 }}>
        <PageHeader
          title={t('dashboard.liveCases')}
          subtitle={t('dashboard.liveCasesDesc')}
        />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: 16,
            marginBottom: 12,
          }}
        >
          {showcaseCards.map((card) => (
            <article key={card.id} className="card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', gap: 12, marginBottom: 10 }}>
                <img
                  src={`/welcome-assets/assets/icons/${card.icon}.svg`}
                  alt=""
                  width={36}
                  height={36}
                />
                <div>
                  <div style={{ fontSize: 11, color: 'var(--accent-secondary, var(--accent))', fontWeight: 600, textTransform: 'uppercase' }}>
                    {card.vertical}
                  </div>
                  <h3 style={{ fontSize: 15, margin: '4px 0 0' }}>{card.title}</h3>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
                <FeatureTag status="mock" label={t('featureTag.story')} />
                <span className="badge">{card.platform}</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>{card.one_liner}</p>
              <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>{card.metric}</p>
              {card.persona.snippets[0] && (
                <p style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic', borderLeft: '2px solid var(--accent)', paddingLeft: 10 }}>
                  {card.persona.snippets[0].text.slice(0, 120)}
                  {card.persona.snippets[0].text.length > 120 ? '…' : ''}
                </p>
              )}
            </article>
          ))}
        </div>
        <Link to="/showcase" style={{ color: 'var(--accent)', fontSize: 13 }}>
          {t('dashboard.viewAllCases')}
        </Link>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 12 }}>
          ·{' '}
          <a href="/showcase" target="_blank" rel="noopener noreferrer" title={t('showcase.publicVersionHint')}>
            {t('showcase.publicVersionShort')}
          </a>
        </span>
      </section>

      {templates.length > 0 && (
        <section style={{ marginBottom: 32 }}>
          <PageHeader title={t('dashboard.quickStart')} />
          <div className="cards-grid">
            {templates.map((tpl) => (
              <div
                key={tpl.id}
                className="card"
                style={{ cursor: 'pointer', position: 'relative' }}
                onClick={() => handleInstall(tpl.id)}
              >
                {(tpl.tags || []).includes('featured') && (
                  <span className="badge-featured" style={{ position: 'absolute', top: 10, right: 10 }}>
                    {t('dashboard.featured')}
                  </span>
                )}
                <h3 style={{ fontSize: 14, color: 'var(--accent)', marginBottom: 6 }}>{tpl.name}</h3>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{tpl.description.slice(0, 80)}</p>
                <span className="badge" style={{ marginTop: 8 }}>{tpl.category}</span>
              </div>
            ))}
          </div>
          <Link to="/marketplace" style={{ color: 'var(--accent)', fontSize: 13, marginTop: 12, display: 'inline-block' }}>
            {t('common.viewAll')}
          </Link>
        </section>
      )}

      {workflows.length > 0 && (
        <section>
          <PageHeader title={t('dashboard.recentWorkflows')} />
          <div className="cards-grid">
            {workflows.map((wf) => (
              <Link key={wf.id} to={`/workflows/${wf.id}`} className="card" style={{ display: 'block' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <h3 style={{ fontSize: 14, color: 'var(--accent)' }}>{wf.name}</h3>
                  <span className={`badge ${wf.status === 'active' ? 'badge-success' : ''}`}>{wf.status}</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
