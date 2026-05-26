import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { installTemplate, ApiError, type Template } from '../api/appClient';
import WorkflowThumbnail from '../components/WorkflowThumbnail';
import FeatureTag from '../components/ui/FeatureTag';
import { useToast } from '../components/ui/Toast';
import { appRoute } from '../lib/routes';
import { t } from '../i18n';

export default function PublicTemplatePage() {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [template, setTemplate] = useState<Template | null>(null);
  const [error, setError] = useState('');
  const [installing, setInstalling] = useState(false);
  const [loadedFromApi, setLoadedFromApi] = useState(false);

  useEffect(() => {
    if (!templateId) return;
    fetch(`/api/public/templates/${templateId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('Not found'))))
      .then((tpl) => {
        setTemplate(tpl);
        setLoadedFromApi(true);
      })
      .catch(() => setError(t('publicTemplate.notFound')));
  }, [templateId]);

  const handleInstall = async () => {
    if (!templateId) return;
    setInstalling(true);
    try {
      const result = await installTemplate(templateId);
      navigate(appRoute(`/workflows/${result.workflow.id}`));
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        const loginUrl = `/login?next=${encodeURIComponent(`/app/share/templates/${templateId}`)}`;
        window.location.href = loginUrl;
      } else {
        showToast(t('publicTemplate.installFailed'), 'error');
      }
    } finally {
      setInstalling(false);
    }
  };

  if (error) {
    return (
      <div style={{ padding: 40, maxWidth: 720, margin: '40px auto' }}>
        <div className="card">
          <h1>{error}</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>{t('publicTemplate.unavailable')}</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate(appRoute('/'))}>
            {t('publicTemplate.openApp')}
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>{t('publicTemplate.shared')}</p>
        <FeatureTag status={loadedFromApi ? 'beta' : 'mock'} label={t('publicTemplate.previewOnly')} showDot={false} />
      </div>
      <h1 style={{ marginBottom: 8 }}>{template.name}</h1>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 16 }}>
        <span className="badge">{template.category}</span>
        {template.tags?.slice(0, 3).map((tag) => (
          <span key={tag} className="badge">{tag}</span>
        ))}
      </div>
      <p style={{ marginBottom: 20, lineHeight: 1.6 }}>{template.description}</p>

      <div className="card" style={{ marginBottom: 20 }}>
        <h2 style={{ fontSize: 14, marginBottom: 12 }}>{t('publicTemplate.preview')}</h2>
        <WorkflowThumbnail definition={template.definition} height={220} />
        <div style={{ display: 'flex', gap: 16, marginTop: 12, fontSize: 12, color: 'var(--text-muted)' }}>
          <span>{template.definition?.nodes?.length || 0} {t('publicTemplate.nodes')}</span>
          <span>{template.definition?.edges?.length || 0} {t('publicTemplate.connections')}</span>
          <span>{template.installs} {t('publicTemplate.installs')}</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={handleInstall} disabled={installing}>
          {installing ? t('publicTemplate.installing') : t('publicTemplate.signInInstall')}
        </button>
        <button
          className="btn"
          onClick={() => {
            navigator.clipboard?.writeText(window.location.href);
            showToast(t('common.success'));
          }}
        >
          {t('publicTemplate.copyLink')}
        </button>
      </div>

      <details style={{ marginTop: 24 }}>
        <summary style={{ cursor: 'pointer', fontSize: 12, color: 'var(--text-muted)' }}>{t('publicTemplate.viewJson')}</summary>
        <pre style={{ marginTop: 8, padding: 12, background: 'var(--bg-secondary)', borderRadius: 6, fontSize: 11, overflowX: 'auto' }}>
          {JSON.stringify(template.definition, null, 2)}
        </pre>
      </details>
    </div>
  );
}
