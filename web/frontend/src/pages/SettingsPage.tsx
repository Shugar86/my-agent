import { useEffect, useState } from 'react';
import {
  listIntegrations,
  saveIntegrationCredentials,
  testIntegration,
  deleteIntegration,
  getIntegrationAuthUrl,
  getAppConfig,
  saveAppConfig,
  getMe,
  getBillingPlan,
  listApiKeys,
  saveApiKey,
  deleteApiKey,
  type Integration,
  type MeUser,
  type BillingPlan,
  type ApiKeyEntry,
} from '../api/appClient';
import PageHeader from '../components/ui/PageHeader';
import { useToast } from '../components/ui/Toast';
import { t } from '../i18n';

type TabId = 'integrations' | 'models' | 'workspace' | 'apiKeys' | 'billing';

interface ConnectionDraft {
  [field: string]: string;
}

const DEFAULT_MODEL_PROFILE = 'kimi';

/** Settings with tabs: integrations, models/API keys, workspace profile. */
export default function SettingsPage() {
  const { showToast } = useToast();
  const [tab, setTab] = useState<TabId>('integrations');
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [drafts, setDrafts] = useState<Record<string, ConnectionDraft>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [primaryModel, setPrimaryModel] = useState(DEFAULT_MODEL_PROFILE);
  const [modelOptions, setModelOptions] = useState<Array<{ value: string; label: string }>>([
    { value: 'kimi', label: 'Kimi K2.6 Code' },
  ]);
  const [me, setMe] = useState<MeUser | null>(null);
  const [billing, setBilling] = useState<BillingPlan | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKeyEntry[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyValue, setNewKeyValue] = useState('');

  const refresh = () => {
    listIntegrations().then(setIntegrations).catch(() => setIntegrations([]));
  };

  useEffect(() => {
    fetch('/api/health').then((r) => r.json()).then(setHealth).catch(() => setHealth(null));
    refresh();
    getAppConfig().then((cfg) => {
      setPrimaryModel(cfg.model?.primary || DEFAULT_MODEL_PROFILE);
      setApiKey(cfg.model?.api_key || '');
    }).catch(() => {});
    fetch('/api/models')
      .then((r) => (r.ok ? r.json() : { profiles: {} }))
      .then((data) => {
        const profiles = data.profiles || {};
        const options = Object.entries(profiles).map(([key, label]) => ({
          value: key,
          label: String(label),
        }));
        if (options.length > 0) setModelOptions(options);
      })
      .catch(() => {});
    getMe().then(setMe).catch(() => {});
    getBillingPlan().then(setBilling).catch(() => setBilling(null));
    listApiKeys().then((data) => setApiKeys(data.keys || [])).catch(() => setApiKeys([]));
  }, []);

  const handleField = (provider: string, name: string, value: string) => {
    setDrafts((prev) => ({ ...prev, [provider]: { ...(prev[provider] || {}), [name]: value } }));
  };

  const handleSave = async (integ: Integration) => {
    setBusy(integ.provider);
    try {
      await saveIntegrationCredentials(integ.provider, drafts[integ.provider] || {});
      showToast(t('settings.saved'));
      refresh();
    } catch {
      showToast(t('settings.saveFailed'), 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleTest = async (integ: Integration) => {
    setBusy(integ.provider);
    try {
      const result = await testIntegration(integ.provider);
      showToast(result.success ? `${integ.name} OK` : t('settings.testFailed'), result.success ? 'success' : 'error');
    } catch {
      showToast(t('settings.testFailed'), 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleOAuth = async (integ: Integration) => {
    try {
      const { auth_url } = await getIntegrationAuthUrl(integ.provider);
      window.location.href = auth_url;
    } catch {
      showToast(t('settings.oauthFailed'), 'error');
    }
  };

  const handleDelete = async (integ: Integration) => {
    if (!window.confirm(t('settings.disconnectConfirm', { name: integ.name }))) return;
    setBusy(integ.provider);
    try {
      await deleteIntegration(integ.provider);
      showToast(t('common.success'));
      refresh();
    } finally {
      setBusy(null);
    }
  };

  const handleSaveModels = async () => {
    setBusy('models');
    try {
      await saveAppConfig({ model: { primary: primaryModel, api_key: apiKey } });
      showToast(t('settings.saved'));
    } catch {
      showToast(t('settings.saveFailed'), 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleAddApiKey = async () => {
    if (!newKeyName.trim() || !newKeyValue.trim()) return;
    setBusy('apikey');
    try {
      await saveApiKey(newKeyName.trim(), newKeyValue.trim());
      setNewKeyName('');
      setNewKeyValue('');
      const data = await listApiKeys();
      setApiKeys(data.keys || []);
      showToast(t('settings.saved'));
    } catch {
      showToast(t('settings.saveFailed'), 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleDeleteApiKey = async (name: string) => {
    setBusy(name);
    try {
      await deleteApiKey(name);
      const data = await listApiKeys();
      setApiKeys(data.keys || []);
      showToast(t('common.success'));
    } catch {
      showToast(t('common.error'), 'error');
    } finally {
      setBusy(null);
    }
  };

  const tabs: { id: TabId; label: string }[] = [
    { id: 'integrations', label: t('settings.tabs.integrations') },
    { id: 'models', label: t('settings.tabs.models') },
    { id: 'apiKeys', label: t('settings.tabs.apiKeys') },
    { id: 'billing', label: t('settings.tabs.billing') },
    { id: 'workspace', label: t('settings.tabs.workspace') },
  ];

  return (
    <div className="page-content" style={{ maxWidth: 920 }}>
      <PageHeader title={t('settings.title')} subtitle={t('settings.subtitle')} />

      <div className="tabs" role="tablist">
        {tabs.map((tb) => (
          <button
            key={tb.id}
            type="button"
            role="tab"
            aria-selected={tab === tb.id}
            className={`tab ${tab === tb.id ? 'active' : ''}`}
            onClick={() => setTab(tb.id)}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {tab === 'integrations' && (
        <>
          <div className="cards-grid">
            {integrations.map((integ) => {
              const draft = drafts[integ.provider] || {};
              return (
                <div key={integ.provider} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <h3 style={{ fontSize: 15 }}>{integ.name}</h3>
                    <span className={`badge ${integ.configured ? 'badge-success' : 'badge-danger'}`}>
                      {integ.configured ? t('common.connected') : t('common.notConnected')}
                    </span>
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>{integ.description}</p>
                  {integ.auth_method === 'oauth' ? (
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button type="button" className="btn btn-primary" onClick={() => handleOAuth(integ)}>
                        {integ.configured ? t('settings.reauthorize') : t('settings.connectOAuth')}
                      </button>
                      {integ.configured && (
                        <button type="button" className="btn" onClick={() => handleDelete(integ)} disabled={busy === integ.provider}>{t('common.disconnect')}</button>
                      )}
                    </div>
                  ) : integ.fields.length > 0 ? (
                    <>
                      {integ.fields.map((f) => (
                        <div key={f.name} className="form-group">
                          <label>{f.label}</label>
                          <input
                            className="input"
                            type={f.type === 'password' ? 'password' : 'text'}
                            value={draft[f.name] || ''}
                            placeholder={integ.configured ? '•••' : f.help}
                            onChange={(e) => handleField(integ.provider, f.name, e.target.value)}
                          />
                        </div>
                      ))}
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button type="button" className="btn btn-primary" onClick={() => handleSave(integ)} disabled={busy === integ.provider}>
                          {busy === integ.provider ? t('settings.saving') : t('common.save')}
                        </button>
                        {integ.configured && (
                          <>
                            <button type="button" className="btn" onClick={() => handleTest(integ)} disabled={busy === integ.provider}>{t('common.test')}</button>
                            <button type="button" className="btn" onClick={() => handleDelete(integ)} disabled={busy === integ.provider}>{t('common.disconnect')}</button>
                          </>
                        )}
                      </div>
                    </>
                  ) : (
                    <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('settings.noCredentials')}</p>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      {tab === 'models' && (
        <div className="card">
          <div className="form-group">
            <label>{t('settings.apiKey')}</label>
            <input className="input" type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="sk-or-…" />
          </div>
          <div className="form-group">
            <label>{t('settings.primaryModel')}</label>
            <select className="input" value={primaryModel} onChange={(e) => setPrimaryModel(e.target.value)}>
              {modelOptions.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <button type="button" className="btn btn-primary" onClick={handleSaveModels} disabled={busy === 'models'}>{t('common.save')}</button>
        </div>
      )}

      {tab === 'workspace' && (
        <>
          <div className="card" style={{ marginBottom: 16 }}>
            <h2 style={{ fontSize: 15, marginBottom: 12 }}>{t('settings.systemStatus')}</h2>
            {health ? (
              <pre style={{ fontSize: 12, color: 'var(--text-muted)', overflow: 'auto', maxHeight: 180 }}>
                {JSON.stringify(health, null, 2)}
              </pre>
            ) : (
              <div className="skeleton" style={{ height: 60 }} />
            )}
          </div>
          <div className="card">
            <h2 style={{ fontSize: 15, marginBottom: 12 }}>{t('settings.workspaceInfo')}</h2>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{me?.username} · {me?.email || '—'}</p>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 8 }}>{t('settings.version')}: 3.3.0</p>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{t('settings.framework')}: FastAPI</p>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{t('settings.defaultModel')}: {primaryModel}</p>
          </div>
        </>
      )}

      {tab === 'apiKeys' && (
        <div className="card">
          <h2 style={{ fontSize: 15, marginBottom: 12 }}>{t('settings.tabs.apiKeys')}</h2>
          {apiKeys.length === 0 && (
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>{t('settings.apiKeyEmpty')}</p>
          )}
          {apiKeys.map((key) => (
            <div key={key.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontFamily: 'monospace', fontSize: 13 }}>{key.name}</span>
              <button type="button" className="btn" onClick={() => handleDeleteApiKey(key.name)} disabled={busy === key.name}>
                {t('common.delete')}
              </button>
            </div>
          ))}
          <div className="form-group" style={{ marginTop: 16 }}>
            <label>{t('settings.apiKeyName')}</label>
            <input className="input" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} placeholder="OPENROUTER_API_KEY" />
          </div>
          <div className="form-group">
            <label>{t('settings.apiKeyValue')}</label>
            <input className="input" type="password" value={newKeyValue} onChange={(e) => setNewKeyValue(e.target.value)} />
          </div>
          <button type="button" className="btn btn-primary" onClick={handleAddApiKey} disabled={busy === 'apikey'}>
            {t('settings.apiKeyAdd')}
          </button>
        </div>
      )}

      {tab === 'billing' && (
        <div className="card">
          <h2 style={{ fontSize: 15, marginBottom: 12 }}>{t('settings.billingPlan')}</h2>
          {billing ? (
            <>
              <p style={{ fontSize: 22, color: 'var(--accent)', fontWeight: 600, marginBottom: 8 }}>{billing.label}</p>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
                {billing.workspace_name || me?.username || '—'}
              </p>
              <p style={{ fontSize: 14 }}>
                {t('settings.billingUsage')}: {billing.workflow_runs_used}
                {billing.workflow_runs_limit != null ? ` / ${billing.workflow_runs_limit}` : ''}
              </p>
              {!billing.allowed && (
                <p style={{ fontSize: 13, color: '#f85149', marginTop: 12 }}>{t('settings.billingLimitReached')}</p>
              )}
            </>
          ) : (
            <div className="skeleton" style={{ height: 80 }} />
          )}
        </div>
      )}
    </div>
  );
}
