import { useEffect, useState } from 'react';
import {
  listIntegrations,
  saveIntegrationCredentials,
  testIntegration,
  deleteIntegration,
  getIntegrationAuthUrl,
  type Integration,
} from '../api/appClient';

interface ConnectionDraft {
  [field: string]: string;
}

export default function SettingsPage() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [drafts, setDrafts] = useState<Record<string, ConnectionDraft>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [toast, setToast] = useState('');

  const refresh = () => {
    listIntegrations().then(setIntegrations).catch(() => setIntegrations([]));
  };

  useEffect(() => {
    fetch('/api/health').then((r) => r.json()).then(setHealth).catch(() => setHealth(null));
    refresh();
  }, []);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(''), 2500);
  };

  const handleField = (provider: string, name: string, value: string) => {
    setDrafts((prev) => ({ ...prev, [provider]: { ...(prev[provider] || {}), [name]: value } }));
  };

  const handleSave = async (integ: Integration) => {
    setBusy(integ.provider);
    try {
      await saveIntegrationCredentials(integ.provider, drafts[integ.provider] || {});
      showToast(`${integ.name} saved`);
      refresh();
    } catch {
      showToast('Save failed');
    } finally {
      setBusy(null);
    }
  };

  const handleTest = async (integ: Integration) => {
    setBusy(integ.provider);
    try {
      const result = await testIntegration(integ.provider);
      showToast(result.success ? `${integ.name} OK` : `${integ.name} test failed`);
    } catch {
      showToast('Test failed');
    } finally {
      setBusy(null);
    }
  };

  const handleOAuth = async (integ: Integration) => {
    try {
      const { auth_url } = await getIntegrationAuthUrl(integ.provider);
      window.location.href = auth_url;
    } catch {
      showToast('OAuth start failed');
    }
  };

  const handleDelete = async (integ: Integration) => {
    if (!window.confirm(`Disconnect ${integ.name}?`)) return;
    setBusy(integ.provider);
    try {
      await deleteIntegration(integ.provider);
      showToast('Disconnected');
      refresh();
    } finally {
      setBusy(null);
    }
  };

  return (
    <div style={{ padding: 30, maxWidth: 920 }}>
      <h1 style={{ marginBottom: 8 }}>Settings</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>Workspace configuration & integrations</p>

      <div className="card" style={{ marginBottom: 16 }}>
        <h2 style={{ fontSize: 15, marginBottom: 12 }}>System Status</h2>
        {health ? (
          <pre style={{ fontSize: 12, color: 'var(--text-muted)', overflow: 'auto', maxHeight: 180 }}>
            {JSON.stringify(health, null, 2)}
          </pre>
        ) : (
          <div className="skeleton" style={{ height: 60 }} />
        )}
      </div>

      <h2 style={{ fontSize: 17, marginBottom: 12 }}>Integrations</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}>
        {integrations.map((integ) => {
          const draft = drafts[integ.provider] || {};
          return (
            <div key={integ.provider} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 8 }}>
                <div>
                  <h3 style={{ fontSize: 15, marginBottom: 4 }}>{integ.name}</h3>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    {integ.category} · {integ.auth_method}
                  </span>
                </div>
                <span
                  style={{
                    fontSize: 11,
                    padding: '3px 8px',
                    borderRadius: 12,
                    background: integ.configured ? 'rgba(35,134,54,0.15)' : 'rgba(248,81,73,0.15)',
                    color: integ.configured ? '#7ee787' : '#ffa198',
                    border: `1px solid ${integ.configured ? '#238636' : '#f85149'}`,
                  }}
                >
                  {integ.configured ? 'Connected' : 'Not connected'}
                </span>
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>{integ.description}</p>
              {integ.actions.length > 0 && (
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 12 }}>
                  {integ.actions.slice(0, 4).map((a) => (
                    <span
                      key={a}
                      style={{
                        fontSize: 10,
                        padding: '2px 6px',
                        background: 'var(--bg)',
                        border: '1px solid var(--border)',
                        borderRadius: 8,
                        color: 'var(--text-muted)',
                      }}
                    >
                      {a}
                    </span>
                  ))}
                </div>
              )}
              {integ.auth_method === 'oauth' ? (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <button className="btn btn-primary" onClick={() => handleOAuth(integ)}>
                    {integ.configured ? 'Reauthorize' : 'Connect via OAuth'}
                  </button>
                  {integ.configured && (
                    <button className="btn" onClick={() => handleDelete(integ)} disabled={busy === integ.provider}>
                      Disconnect
                    </button>
                  )}
                </div>
              ) : integ.fields.length > 0 ? (
                <>
                  {integ.fields.map((f) => (
                    <div key={f.name} style={{ marginBottom: 8 }}>
                      <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 2 }}>
                        {f.label} {f.required && <span style={{ color: '#f85149' }}>*</span>}
                      </label>
                      <input
                        className="input"
                        type={f.type === 'password' ? 'password' : 'text'}
                        value={draft[f.name] || ''}
                        placeholder={integ.configured ? '••• already set' : f.help}
                        onChange={(e) => handleField(integ.provider, f.name, e.target.value)}
                      />
                      {f.help && (
                        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{f.help}</p>
                      )}
                    </div>
                  ))}
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button className="btn btn-primary" onClick={() => handleSave(integ)} disabled={busy === integ.provider}>
                      {busy === integ.provider ? 'Saving...' : 'Save'}
                    </button>
                    {integ.configured && (
                      <>
                        <button className="btn" onClick={() => handleTest(integ)} disabled={busy === integ.provider}>
                          Test
                        </button>
                        <button className="btn" onClick={() => handleDelete(integ)} disabled={busy === integ.provider}>
                          Disconnect
                        </button>
                      </>
                    )}
                  </div>
                </>
              ) : (
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>No credentials required.</p>
              )}
              {integ.docs_url && (
                <a
                  href={integ.docs_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ display: 'block', fontSize: 11, color: 'var(--accent)', marginTop: 8 }}
                >
                  Setup docs →
                </a>
              )}
            </div>
          );
        })}
      </div>

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
