import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listWorkflows } from '../api/workflowClient';
import type { Workflow } from '../types/workflow';
import { t } from '../i18n';

export default function WorkflowList() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listWorkflows()
      .then(setWorkflows)
      .catch(() => setWorkflows([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ padding: 30 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, marginBottom: 4 }}>{t('workflows.title')}</h1>
          <p style={{ color: 'var(--text-muted)' }}>{t('workflows.subtitle')}</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/workflows/new')}>{t('workflows.new')}</button>
      </div>

      {loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
          {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 100 }} />)}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {workflows.map((wf) => (
          <div
            key={wf.id}
            className="card"
            onClick={() => navigate(`/workflows/${wf.id}`)}
            style={{ cursor: 'pointer' }}
          >
            <h3 style={{ marginBottom: 8 }}>{wf.name}</h3>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              {wf.definition.nodes.length} {t('workflows.nodes')} · <span style={{ color: wf.status === 'active' ? 'var(--success)' : 'var(--text-muted)' }}>{wf.status}</span>
            </p>
          </div>
        ))}
      </div>

      {!loading && workflows.length === 0 && (
        <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>
          <p>{t('workflows.empty')}</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/workflows/new')}>
            {t('workflows.emptyCta')}
          </button>
        </div>
      )}
    </div>
  );
}
