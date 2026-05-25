import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listAgents, listTemplates, installTemplate, getHealth } from '../api/appClient';
import { listWorkflows } from '../api/workflowClient';

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState<Array<{ id: string; name: string; role?: string }>>([]);
  const [templates, setTemplates] = useState<Array<{ id: string; name: string; description: string; category: string }>>([]);
  const [stats, setStats] = useState({ agents: 0, workflows: 0, templates: 0 });

  useEffect(() => {
    Promise.all([
      listAgents().catch(() => []),
      listTemplates(undefined, 'popular').catch(() => []),
      listWorkflows().catch(() => []),
      getHealth().catch(() => ({})),
    ]).then(([agentList, tplList, wfList]) => {
      setAgents(Array.isArray(agentList) ? agentList.slice(0, 6) : []);
      setTemplates(Array.isArray(tplList) ? tplList.slice(0, 4) : []);
      setStats({
        agents: Array.isArray(agentList) ? agentList.length : 0,
        workflows: wfList.length,
        templates: Array.isArray(tplList) ? tplList.length : 0,
      });
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
      <h1 style={{ marginBottom: 8 }}>Dashboard</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>Your AI automation hub</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 32 }}>
        {[
          { label: 'Agents', value: stats.agents },
          { label: 'Workflows', value: stats.workflows },
          { label: 'Templates', value: stats.templates },
        ].map((s) => (
          <div key={s.label} className="card">
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.label}</div>
            <div style={{ fontSize: 28, color: 'var(--accent)', fontWeight: 600 }}>{s.value}</div>
          </div>
        ))}
      </div>

      <section style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>Quick Templates</h2>
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
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
          {agents.map((a) => (
            <Link key={a.id} to={`/chat?agent=${a.id}`} className="card" style={{ display: 'block' }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>🤖</div>
              <h3 style={{ fontSize: 14 }}>{a.name || a.id}</h3>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.role?.slice(0, 60) || 'AI Agent'}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
