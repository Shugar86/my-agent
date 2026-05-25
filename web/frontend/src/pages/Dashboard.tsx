import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listAgents, listTemplates, installTemplate, getHealth, listIntegrations, type Integration } from '../api/appClient';
import { listWorkflows } from '../api/workflowClient';
import type { Workflow } from '../types/workflow';
import DemoModal from '../components/DemoModal';

interface Stat {
  label: string;
  value: number | string;
  hint?: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
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
      <DemoModal open={demoOpen} onClose={() => setDemoOpen(false)} />

      <section
        style={{
          background: 'linear-gradient(135deg, rgba(31,111,235,0.18) 0%, rgba(35,134,54,0.10) 50%, rgba(234,75,113,0.10) 100%)',
          border: '1px solid var(--border)',
          borderRadius: 14,
          padding: '28px 32px',
          marginBottom: 28,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 24,
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ flex: '1 1 320px' }}>
          <div style={{ fontSize: 11, letterSpacing: 1.4, textTransform: 'uppercase', color: 'var(--accent)', marginBottom: 6 }}>
            Autonomous Workflow OS
          </div>
          <h1 style={{ fontSize: 26, margin: 0, marginBottom: 8 }}>
            From a webhook to a competitive brief in 90 seconds.
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, maxWidth: 560 }}>
            Multi-agent research, comparative analysis, DOCX report and an n8n trigger —
            replacing ~4 hours of analyst work in a single click.
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'flex-end' }}>
          <button type="button" className="btn btn-primary" onClick={() => setDemoOpen(true)} style={{ fontSize: 14, padding: '10px 18px' }}>
            ▶ Try 90s demo
          </button>
          <div style={{ display: 'flex', gap: 8 }}>
            <Link to="/workflows/new" className="btn">+ New workflow</Link>
            <Link to="/marketplace" className="btn">Marketplace</Link>
          </div>
        </div>
      </section>

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
            <div key={t.id} className="card" style={{ cursor: 'pointer', position: 'relative' }} onClick={() => handleInstall(t.id)}>
              {(t.tags || []).includes('featured') && (
                <span className="badge-featured" style={{ position: 'absolute', top: 10, right: 10 }}>Featured</span>
              )}
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
