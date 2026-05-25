import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listAgents, listTemplates, installTemplate, getHealth, listIntegrations, type Integration } from '../api/appClient';
import { listWorkflows } from '../api/workflowClient';
import type { Workflow } from '../types/workflow';

interface Stat {
  label: string;
  value: number | string;
  hint?: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState<Array<{ id: string; name: string; role?: string }>>([]);
  const [templates, setTemplates] = useState<Array<{ id: string; name: string; description: string; category: string }>>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [stats, setStats] = useState<Stat[]>([]);

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
        { label: 'Active workflows', value: active, hint: `${safeWfs.length} total` },
        { label: 'Templates', value: safeTpls.length, hint: 'in marketplace' },
        { label: 'Integrations', value: `${connected}/${safeIntegs.length}`, hint: 'connected' },
        { label: 'Agents', value: safeAgents.length, hint: 'available' },
      ]);
      setLoading(false);
    });
  }, []);

  const handleInstall = async (id: string) => {
    try {
      const result = await installTemplate(id);
      navigate(`/workflows/${result.workflow.id}`);
    } catch {
      alert('Install failed');
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 30 }}>
        <div className="skeleton" style={{ height: 40, width: 200, marginBottom: 24 }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {[1, 2, 3, 4].map((i) => <div key={i} className="skeleton" style={{ height: 80 }} />)}
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 30 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ marginBottom: 8 }}>Dashboard</h1>
          <p style={{ color: 'var(--text-muted)' }}>Your AI automation hub — workflows, agents, marketplace.</p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Link to="/workflows/new" className="btn btn-primary">+ New workflow</Link>
          <Link to="/marketplace" className="btn">Browse marketplace</Link>
          <a
            href="https://render.com/deploy"
            target="_blank"
            rel="noreferrer"
            className="btn"
            title="Deploy a fork to Render in one click"
          >
            Deploy to cloud →
          </a>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 32 }}>
        {stats.map((s) => (
          <div key={s.label} className="card">
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.label}</div>
            <div style={{ fontSize: 28, color: 'var(--accent)', fontWeight: 600 }}>{s.value}</div>
            {s.hint && <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.hint}</div>}
          </div>
        ))}
      </div>

      {workflows.length > 0 && (
        <section style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>Recent workflows</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
            {workflows.map((wf) => (
              <Link key={wf.id} to={`/workflows/${wf.id}`} className="card" style={{ display: 'block' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <h3 style={{ fontSize: 14, color: 'var(--accent)' }}>{wf.name}</h3>
                  <span
                    style={{
                      fontSize: 10,
                      padding: '2px 6px',
                      borderRadius: 8,
                      background: wf.status === 'active' ? 'rgba(35,134,54,0.2)' : 'var(--bg-tertiary)',
                      color: wf.status === 'active' ? '#7ee787' : 'var(--text-muted)',
                    }}
                  >
                    {wf.status}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {wf.definition?.nodes?.length || 0} nodes · {wf.definition?.edges?.length || 0} edges
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>Quick start templates</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
          {templates.map((t) => (
            <div key={t.id} className="card" style={{ cursor: 'pointer' }} onClick={() => handleInstall(t.id)}>
              <h3 style={{ fontSize: 14, color: 'var(--accent)', marginBottom: 6 }}>{t.name}</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t.description.slice(0, 80)}</p>
              <span style={{ fontSize: 11, background: 'var(--bg-tertiary)', padding: '2px 8px', borderRadius: 12, marginTop: 8, display: 'inline-block' }}>{t.category}</span>
            </div>
          ))}
        </div>
        <Link to="/marketplace" style={{ color: 'var(--accent)', fontSize: 13, marginTop: 12, display: 'inline-block' }}>View all templates →</Link>
      </section>

      <section>
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>Agents</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
          {agents.map((a) => (
            <Link key={a.id} to={`/chat?agent=${a.id}`} className="card" style={{ display: 'block' }}>
              <div
                style={{
                  width: 36, height: 36, borderRadius: 8,
                  background: 'linear-gradient(135deg, var(--accent), #1f6feb)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontWeight: 700, marginBottom: 8,
                }}
              >
                {(a.name || a.id).slice(0, 2).toUpperCase()}
              </div>
              <h3 style={{ fontSize: 14 }}>{a.name || a.id}</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.role?.slice(0, 60) || 'AI Agent'}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
