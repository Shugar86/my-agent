import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  listTeams,
  createTeam,
  acceptInvite,
  listTemplates,
  installTemplate,
  completeOnboarding,
  listIntegrations,
  saveIntegrationCredentials,
  testIntegration,
  getIntegrationAuthUrl,
  type Integration,
  type Template,
} from '../api/appClient';

const STEPS = ['Workspace', 'Integrations', 'First workflow', 'Test run'] as const;

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [step, setStep] = useState(1);
  const [teamName, setTeamName] = useState('');
  const [teams, setTeams] = useState<Array<{ id: string; name: string }>>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [status, setStatus] = useState('');
  const [installing, setInstalling] = useState(false);
  const [installedWfId, setInstalledWfId] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, Record<string, string>>>({});
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const invite = params.get('invite');
    if (invite) {
      acceptInvite(invite)
        .then(() => setStatus('Invite accepted!'))
        .catch(() => setStatus('Invalid invite'));
    }
    listTeams().then((d) => setTeams(d.teams)).catch(() => {});
    listIntegrations().then(setIntegrations).catch(() => {});
    listTemplates(undefined, 'popular').then((t) => setTemplates(t.slice(0, 6))).catch(() => {});
  }, [params]);

  const handleCreateTeam = async () => {
    if (!teamName.trim()) return;
    await createTeam(teamName.trim());
    setStep(2);
  };

  const handleConnectOAuth = async (provider: string) => {
    try {
      const data = await getIntegrationAuthUrl(provider);
      if (data.auth_url) window.location.href = data.auth_url;
    } catch {
      setStatus('OAuth not configured');
    }
  };

  const handleSaveApiKey = async (integ: Integration) => {
    const draft = drafts[integ.provider] || {};
    if (Object.values(draft).every((v) => !v)) return;
    try {
      await saveIntegrationCredentials(integ.provider, draft);
      const refreshed = await listIntegrations();
      setIntegrations(refreshed);
      setStatus(`${integ.name} saved`);
    } catch {
      setStatus('Save failed');
    }
  };

  const handleTest = async (provider: string) => {
    setTesting(provider);
    try {
      const result = await testIntegration(provider);
      setTestResults((prev) => ({ ...prev, [provider]: !!result.success }));
      setStatus(result.success ? 'Connection OK' : 'Connection failed');
    } catch {
      setStatus('Test failed');
    } finally {
      setTesting(null);
    }
  };

  const handleInstall = async (id: string) => {
    setInstalling(true);
    try {
      const result = await installTemplate(id);
      setInstalledWfId(result.workflow.id);
      setStep(4);
    } finally {
      setInstalling(false);
    }
  };

  const handleTestRun = async () => {
    if (!installedWfId) return;
    try {
      await fetch(`/api/workflows/${installedWfId}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload: { test: true } }),
      });
      await completeOnboarding();
      navigate(`/workflows/${installedWfId}`);
    } catch {
      setStatus('Test run failed');
    }
  };

  const finish = async () => {
    await completeOnboarding();
    navigate('/');
  };

  return (
    <div style={{ padding: 30, maxWidth: 760, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 8 }}>Welcome to My Agent</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 16 }}>Get to your first running workflow in under 5 minutes.</p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {STEPS.map((label, i) => {
          const idx = i + 1;
          const active = idx === step;
          const done = idx < step;
          return (
            <div
              key={label}
              style={{
                flex: 1,
                padding: 10,
                borderRadius: 6,
                fontSize: 12,
                background: active ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
                border: `1px solid ${active ? 'var(--accent)' : done ? 'var(--success)' : 'var(--border)'}`,
                color: active ? 'var(--text)' : 'var(--text-muted)',
                textAlign: 'center',
              }}
            >
              {done ? '✓ ' : `${idx}. `}
              {label}
            </div>
          );
        })}
      </div>

      {status && <p style={{ color: 'var(--accent)', marginBottom: 16 }}>{status}</p>}

      {step === 1 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>Your workspace</h2>
          {teams.length > 0 ? (
            <>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
                You're in: <strong>{teams[0].name}</strong>
              </p>
              <button type="button" className="btn btn-primary" onClick={() => setStep(2)}>Continue</button>
            </>
          ) : (
            <>
              <input className="input" placeholder="Team name" value={teamName} onChange={(e) => setTeamName(e.target.value)} style={{ marginBottom: 12 }} />
              <button type="button" className="btn btn-primary" onClick={handleCreateTeam}>Create team</button>
            </>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>Connect services (optional)</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
            Connect at least one integration to use real actions. You can also configure these later in Settings.
          </p>
          <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
            {integrations.filter((i) => i.fields.length > 0 || i.auth_method === 'oauth').map((integ) => {
              const draft = drafts[integ.provider] || {};
              return (
                <div key={integ.provider} style={{ border: '1px solid var(--border)', borderRadius: 8, padding: 12, background: 'var(--bg)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 6 }}>
                    <strong style={{ fontSize: 13 }}>{integ.name}</strong>
                    <span style={{ fontSize: 10, color: integ.configured ? 'var(--success)' : 'var(--text-muted)' }}>
                      {integ.configured ? '● connected' : '○ not connected'}
                    </span>
                  </div>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>{integ.description}</p>
                  {integ.auth_method === 'oauth' ? (
                    <button type="button" className="btn" onClick={() => handleConnectOAuth(integ.provider)} style={{ width: '100%' }}>
                      {integ.configured ? 'Reauthorize' : 'Connect'}
                    </button>
                  ) : (
                    <>
                      {integ.fields.map((f) => (
                        <input
                          key={f.name}
                          className="input"
                          placeholder={f.label}
                          type={f.type === 'password' ? 'password' : 'text'}
                          value={draft[f.name] || ''}
                          onChange={(e) =>
                            setDrafts((prev) => ({
                              ...prev,
                              [integ.provider]: { ...(prev[integ.provider] || {}), [f.name]: e.target.value },
                            }))
                          }
                          style={{ marginBottom: 6 }}
                        />
                      ))}
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button type="button" className="btn btn-primary" onClick={() => handleSaveApiKey(integ)} style={{ flex: 1 }}>
                          Save
                        </button>
                        {integ.configured && (
                          <button type="button" className="btn" onClick={() => handleTest(integ.provider)} disabled={testing === integ.provider}>
                            {testing === integ.provider
                              ? '...'
                              : testResults[integ.provider] === true
                              ? '✓ Test'
                              : testResults[integ.provider] === false
                              ? '✗ Test'
                              : 'Test'}
                          </button>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
          <button type="button" className="btn btn-primary" onClick={() => setStep(3)} style={{ marginTop: 16 }}>
            Continue
          </button>
        </div>
      )}

      {step === 3 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>Install your first workflow</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
            Pick a template — we'll clone it into your workspace and run it on the next step.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 8 }}>
            {templates.map((t) => (
              <button
                key={t.id}
                type="button"
                className="btn"
                style={{ textAlign: 'left', display: 'block', height: 'auto', padding: 12 }}
                onClick={() => handleInstall(t.id)}
                disabled={installing}
              >
                <strong>{t.name}</strong>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{t.description.slice(0, 80)}</div>
              </button>
            ))}
          </div>
          <button type="button" className="btn btn-primary" style={{ marginTop: 16 }} onClick={finish}>
            Finish without template
          </button>
        </div>
      )}

      {step === 4 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>Run a test execution</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>
            Send a sample payload through your new workflow to verify everything is wired up.
          </p>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn btn-primary" onClick={handleTestRun}>Run test & open builder</button>
            <button type="button" className="btn" onClick={finish}>Skip and go to dashboard</button>
          </div>
        </div>
      )}
    </div>
  );
}
