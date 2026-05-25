import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import WorkflowThumbnail from '../components/WorkflowThumbnail';
import type { Template } from '../api/appClient';

export default function PublicTemplatePage() {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const [template, setTemplate] = useState<Template | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!templateId) return;
    fetch(`/api/public/templates/${templateId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('Not found'))))
      .then(setTemplate)
      .catch(() => setError('Template not found or not published'));
  }, [templateId]);

  if (error) {
    return (
      <div style={{ padding: 40, maxWidth: 720, margin: '40px auto' }}>
        <div className="card">
          <h1>{error}</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>
            The template you're looking for is unavailable.
          </p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/')}>
            Open My Agent
          </button>
        </div>
      </div>
    );
  }

  if (!template) {
    return <div style={{ padding: 40 }}><div className="skeleton" style={{ height: 320 }} /></div>;
  }

  return (
    <div style={{ padding: 40, maxWidth: 720, margin: '40px auto' }}>
      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>Shared workflow template</p>
      <h1 style={{ marginBottom: 8 }}>{template.name}</h1>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 16 }}>
        <span className="badge">{template.category}</span>
        {template.tags?.slice(0, 3).map((tag) => (
          <span key={tag} className="badge">{tag}</span>
        ))}
      </div>
      <p style={{ marginBottom: 20, lineHeight: 1.6 }}>{template.description}</p>

      <div className="card" style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 14, marginBottom: 12 }}>Workflow preview</h2>
        <WorkflowThumbnail definition={template.definition} height={220} />
        <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
          <span>{template.definition?.nodes?.length || 0} nodes</span>
          <span>{template.definition?.edges?.length || 0} connections</span>
          <span>{template.installs} installs</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={() => navigate('/marketplace')}>
          Sign in & install
        </button>
        <button className="btn" onClick={() => navigator.clipboard?.writeText(window.location.href)}>
          Copy share link
        </button>
      </div>

      <details style={{ marginTop: 24 }}>
        <summary style={{ cursor: 'pointer', fontSize: 12, color: 'var(--text-muted)' }}>View JSON definition</summary>
        <pre style={{ marginTop: 8, padding: 12, background: 'var(--bg-secondary)', borderRadius: 6, fontSize: 11, overflowX: 'auto' }}>
          {JSON.stringify(template.definition, null, 2)}
        </pre>
      </details>
    </div>
  );
}
