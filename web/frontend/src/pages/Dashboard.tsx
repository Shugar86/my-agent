import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listAgents, listTemplates, installTemplate, getHealth, listIntegrations, type Integration } from '../api/appClient';
import { listWorkflows } from '../api/workflowClient';
import type { Workflow } from '../types/workflow';
import DemoModal from '../components/DemoModal';
import PageHeader from '../components/ui/PageHeader';
import EmptyState from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { t } from '../i18n';

interface Stat {
  label: string;
  value: number | string;
  hint?: string;
  to?: string;
}

/** Home dashboard with stats, demo hero, templates and agents. */
export default function Dashboard() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState<Array<{ id: string; name: string; role?: string }>>([]);
  const [templates, setTemplates] = useState<Array<{ id: string; name: string; description: string; category: string; tags?: string[] }>>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [stats, setStats] = useState<Stat[]>([]);
  const [demoOpen, setDemoOpen] = useState(false);

  useEffect(() => {
    Promise.all([
      listAgents().catch(() => []),
      listTemplates(undefined, 'popular').catch(() => []),
      listWorkflows().catch(() => []),
      listIntegrations().catch(() => []),
      getHealth().catch(() => ({})),
    ]).then(([agentList, tplList, wfList, integs]) => {
      const safeAgents = Array.isArray(agentList) ? agentList : [];
      const safeTpls = Array.isArray(tplList) ? tplList : [];
      const safeWfs = Array.isArray(wfList) ? wfList : [];
      const safeIntegs = Array.isArray(integs) ? integs : [];
      setAgents(safeAgents.slice(0, 6));
      setTemplates(safeTpls.slice(0, 4));
      setWorkflows(safeWfs.slice(0, 5));
      setIntegrations(safeIntegs);
      const active = safeWfs.filter((w) => w.status === 'active').length;
      const connected = safeIntegs.filter((i) => i.configured).length;
      setStats([
        { label: t('dashboard.activeWorkflows'), value: active, hint: `${safeWfs.length} ${t('dashboard.total')}`, to: '/workflows' },
        { label: t('dashboard.templates'), value: safeTpls.length, hint: t('dashboard.inMarketplace'), to: '/marketplace' },
        { label: t('dashboard.integrations'), value: `${connected}/${safeIntegs.length}`, hint: t('dashboard.connected'), to: '/settings' },
        { label: t('dashboard.agents'), value: safeAgents.length, hint: t('dashboard.available'), to: '/agents' },
      ]);
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
        <div className="skeleton" style={{ height: 40, width: 200, marginBottom: 24 }} />
        <div className="stats-grid">
          {[1, 2, 3, 4].map((i) => <div key={i} className="skeleton" style={{ height: 80 }} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="page-content">
      <DemoModal open={demoOpen} onClose={() => setDemoOpen(false)} />

      <section className="dashboard-hero">
        <div style={{ flex: '1 1 320px' }}>
          <div className="dashboard-hero__badge">{t('dashboard.heroBadge')}</div>
          <h1 className="dashboard-hero__title">{t('dashboard.heroTitle')}</h1>
          <p className="dashboard-hero__desc">{t('dashboard.heroDesc')}</p>
        </div>
        <div className="dashboard-hero__actions">
          <button type="button" className="btn btn-primary" onClick={() => setDemoOpen(true)}>{t('dashboard.tryDemo')}</button>
          <div style={{ display: 'flex', gap: 8 }}>
            <Link to="/workflows/new" className="btn">{t('dashboard.newWorkflow')}</Link>
            <Link to="/marketplace" className="btn">{t('nav.marketplace')}</Link>
          </div>
        </div>
      </section>

      <div className="stats-grid">
        {stats.map((s) => (
          <div
            key={s.label}
            className="card stat-card"
            role={s.to ? 'link' : undefined}
            tabIndex={s.to ? 0 : undefined}
            onClick={() => s.to && navigate(s.to)}
            onKeyDown={(e) => s.to && e.key === 'Enter' && navigate(s.to)}
          >
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.label}</div>
            <div style={{ fontSize: 28, color: 'var(--accent)', fontWeight: 600 }}>{s.value}</div>
            {s.hint && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.hint}</div>}
          </div>
        ))}
      </div>

      {workflows.length > 0 ? (
        <section style={{ marginBottom: 32 }}>
          <PageHeader title={t('dashboard.recentWorkflows')} />
          <div className="cards-grid">
            {workflows.map((wf) => (
              <Link key={wf.id} to={`/workflows/${wf.id}`} className="card" style={{ display: 'block' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <h3 style={{ fontSize: 14, color: 'var(--accent)' }}>{wf.name}</h3>
                  <span className={`badge ${wf.status === 'active' ? 'badge-success' : ''}`}>{wf.status}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {wf.definition?.nodes?.length || 0} nodes · {wf.definition?.edges?.length || 0} edges
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : (
        <EmptyState
          title={t('dashboard.noWorkflows')}
          actionLabel={t('dashboard.noWorkflowsCta')}
          actionTo="/marketplace"
        />
      )}

      <section style={{ marginBottom: 32 }}>
        <PageHeader title={t('dashboard.quickStart')} />
        <div className="cards-grid">
          {templates.map((tpl) => (
            <div key={tpl.id} className="card" style={{ cursor: 'pointer', position: 'relative' }} onClick={() => handleInstall(tpl.id)}>
              {(tpl.tags || []).includes('featured') && (
                <span className="badge-featured" style={{ position: 'absolute', top: 10, right: 10 }}>{t('dashboard.featured')}</span>
              )}
              <h3 style={{ fontSize: 14, color: 'var(--accent)', marginBottom: 6 }}>{tpl.name}</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{tpl.description.slice(0, 80)}</p>
              <span className="badge" style={{ marginTop: 8 }}>{tpl.category}</span>
            </div>
          ))}
        </div>
        <Link to="/marketplace" style={{ color: 'var(--accent)', fontSize: 13, marginTop: 12, display: 'inline-block' }}>{t('common.viewAll')}</Link>
      </section>

      <section>
        <PageHeader title={t('dashboard.agents')} />
        <div className="cards-grid">
          {agents.map((a) => (
            <Link key={a.id} to={`/chat?agent=${a.id}`} className="card" style={{ display: 'block' }}>
              <div className="agent-avatar">{(a.name || a.id).slice(0, 2).toUpperCase()}</div>
              <h3 style={{ fontSize: 14 }}>{a.name || a.id}</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.role?.slice(0, 60) || 'AI Agent'}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
