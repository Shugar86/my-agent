import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  listTeams,
  createTeam,
  acceptInvite,
  installTemplate,
  ApiError,
  completeOnboarding,
  listIntegrations,
  saveIntegrationCredentials,
  testIntegration,
  getIntegrationAuthUrl,
  startDemoRun,
  logUxEvent,
  type Integration,
} from '../api/appClient';
import { getRun } from '../api/workflowClient';
import ExecutionTimeline from '../components/ExecutionTimeline';
import { t } from '../i18n';

const STEP_KEYS = ['demo', 'usecase', 'workspace', 'integrations'] as const;
const TOTAL_STEPS = STEP_KEYS.length;

const USECASE_IDS = ['ararat', 'pegasszn', 'pretenzia', 'my-agent'] as const;

const USECASE_TEMPLATES: Record<(typeof USECASE_IDS)[number], string> = {
  ararat: 'tpl_beauty_consultant',
  pegasszn: 'tpl_content_repurpose',
  pretenzia: 'tpl_lead_qualifier',
  'my-agent': 'tpl_competitor_intelligence',
};

interface ShowcaseCard {
  id: string;
  vertical: string;
  title: string;
  one_liner: string;
  metric: string;
  persona: {
    snippets: Array<{ text: string }>;
  };
}

/** Four-step onboarding: demo first, then use case, workspace, optional integrations. */
export default function OnboardingPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [step, setStep] = useState(1);
  const [teamName, setTeamName] = useState('');
  const [teams, setTeams] = useState<Array<{ id: string; name: string }>>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [usecaseCards, setUsecaseCards] = useState<ShowcaseCard[]>([]);
  const [status, setStatus] = useState('');
  const [installing, setInstalling] = useState(false);
  const [installedWfId, setInstalledWfId] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, Record<string, string>>>({});
  const [testing, setTesting] = useState<string | null>(null);
  const [demoRun, setDemoRun] = useState<{
    workflow_id: string;
    run_id: string;
    mode: 'mock' | 'real';
    artifact_url?: string;
    logs: Array<{ node_id: string; event: string; detail?: unknown }>;
    status: string;
  } | null>(null);
  const [demoStarting, setDemoStarting] = useState(false);

  useEffect(() => {
    logUxEvent('onboarding_start');
    const invite = params.get('invite');
    if (invite) {
      acceptInvite(invite)
        .then(() => setStatus(t('onboarding.inviteAccepted')))
        .catch(() => setStatus(t('onboarding.inviteInvalid')));
    }
    listTeams().then((d) => setTeams(d.teams)).catch(() => {});
    listIntegrations().then(setIntegrations).catch(() => {});
    fetch('/welcome-assets/data/showcase.json')
      .then((r) => (r.ok ? r.json() : { cards: [] }))
      .then((data) => {
        const cards = (data.cards || []) as ShowcaseCard[];
        setUsecaseCards(cards.filter((c) => USECASE_IDS.includes(c.id as (typeof USECASE_IDS)[number])));
      })
      .catch(() => {});
  }, [params]);

  const handleCreateTeam = async () => {
    if (!teamName.trim()) return;
    await createTeam(teamName.trim());
    setStep(4);
  };

  const handleConnectOAuth = async (provider: string) => {
    try {
      const data = await getIntegrationAuthUrl(provider);
      if (data.auth_url) window.location.href = data.auth_url;
    } catch {
      setStatus(t('onboarding.oauthNotConfigured'));
    }
  };

  const handleSaveApiKey = async (integ: Integration) => {
    const draft = drafts[integ.provider] || {};
    if (Object.values(draft).every((v) => !v)) return;
    try {
      await saveIntegrationCredentials(integ.provider, draft);
      const refreshed = await listIntegrations();
      setIntegrations(refreshed);
      setStatus(`${integ.name} ${t('common.success').toLowerCase()}`);
    } catch {
      setStatus(t('onboarding.saveFailed'));
    }
  };

  const handleTest = async (provider: string) => {
    setTesting(provider);
    try {
      const result = await testIntegration(provider);
      setStatus(result.success ? t('onboarding.connectionOk') : t('onboarding.connectionFailed'));
    } catch {
      setStatus(t('onboarding.connectionFailed'));
    } finally {
      setTesting(null);
    }
  };

  const handleUsecaseSelect = async (cardId: string) => {
    const templateId = USECASE_TEMPLATES[cardId as (typeof USECASE_IDS)[number]];
    setInstalling(true);
    setStatus('');
    try {
      if (templateId) {
        const result = await installTemplate(templateId);
        setInstalledWfId(result.workflow.id);
      }
      setStep(3);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        setStatus(t('onboarding.templateNotSeeded'));
        setStep(3);
      } else {
        setStatus(t('dashboard.installFailed'));
      }
    } finally {
      setInstalling(false);
    }
  };

  const handleTestRun = async () => {
    setDemoStarting(true);
    setStatus('');
    try {
      const result = await startDemoRun('Notion', 'Linear', false);
      setDemoRun({
        workflow_id: result.workflow_id,
        run_id: result.run_id,
        mode: result.mode,
        artifact_url: result.artifact_url,
        logs: [],
        status: 'running',
      });
      logUxEvent('onboarding_demo_started');
    } catch {
      setStatus(t('onboarding.demoFailed'));
    } finally {
      setDemoStarting(false);
    }
  };

  useEffect(() => {
    if (!demoRun || demoRun.status !== 'running') return undefined;
    const interval = setInterval(async () => {
      try {
        const run = await getRun(demoRun.workflow_id, demoRun.run_id);
        setDemoRun((prev) =>
          prev ? { ...prev, logs: run.logs || [], status: run.status } : prev,
        );
        if (run.status !== 'running') {
          clearInterval(interval);
          logUxEvent('onboarding_demo_completed', { status: run.status });
        }
      } catch {
        clearInterval(interval);
      }
    }, 800);
    return () => clearInterval(interval);
  }, [demoRun?.run_id, demoRun?.status]);

  const finish = async () => {
    await completeOnboarding();
    logUxEvent('onboarding_complete');
    navigate('/');
  };

  const progressPct = Math.round((step / TOTAL_STEPS) * 100);

  return (
    <div className="page-content" style={{ maxWidth: 760, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 8 }}>{t('onboarding.title')}</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 16 }}>{t('onboarding.subtitle')}</p>

      <div className="onboarding-progress">
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>
          <span>{t('common.stepOf', { current: step, total: TOTAL_STEPS })}</span>
          <span>{progressPct}%</span>
        </div>
        <div className="onboarding-progress__bar">
          <div className="onboarding-progress__fill" style={{ width: `${progressPct}%` }} />
        </div>
        <div className="onboarding-steps" style={{ marginTop: 12 }}>
          {STEP_KEYS.map((key, i) => {
            const idx = i + 1;
            return (
              <div
                key={key}
                className={`onboarding-step ${idx === step ? 'active' : ''} ${idx < step ? 'done' : ''}`}
              >
                {idx < step ? '✓ ' : `${idx}. `}
                {t(`onboarding.steps.${key}`)}
              </div>
            );
          })}
        </div>
      </div>

      {status && <p style={{ color: 'var(--accent)', marginBottom: 16 }}>{status}</p>}

      {step === 1 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>{t('onboarding.demoTitle')}</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>{t('onboarding.demoDesc')}</p>
          {!demoRun ? (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button type="button" className="btn btn-primary" onClick={handleTestRun} disabled={demoStarting}>
                {demoStarting ? t('common.loading') : t('onboarding.runDemo')}
              </button>
              <button type="button" className="btn" onClick={() => setStep(2)}>{t('common.skip')}</button>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, padding: '8px 12px', background: 'var(--bg-tertiary)', borderRadius: 6, fontSize: 12 }}>
                <span>
                  {demoRun.status === 'success' ? '✓' : demoRun.status === 'failed' ? '✗' : '…'}{' '}
                  <strong style={{ color: demoRun.status === 'success' ? 'var(--success)' : demoRun.status === 'failed' ? 'var(--danger)' : 'var(--accent)' }}>
                    {demoRun.status}
                  </strong>
                </span>
                <span style={{ color: 'var(--text-muted)' }}>{demoRun.logs.length} events</span>
              </div>
              <div style={{ maxHeight: 400, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 6, padding: 12 }}>
                <ExecutionTimeline logs={demoRun.logs} />
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
                {demoRun.status !== 'running' && demoRun.artifact_url && (
                  <a href={demoRun.artifact_url} className="btn btn-primary" download target="_blank" rel="noreferrer">
                    {t('onboarding.downloadDocx')}
                  </a>
                )}
                {demoRun.status !== 'running' && (
                  <button type="button" className="btn btn-primary" onClick={() => setStep(2)}>
                    {t('common.continue')}
                  </button>
                )}
                <button type="button" className="btn" onClick={() => navigate(`/workflows/${demoRun.workflow_id}?run=${demoRun.run_id}`)}>
                  {t('onboarding.openInBuilder')}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>{t('onboarding.usecaseTitle')}</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>{t('onboarding.usecaseDesc')}</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 12 }}>
            {usecaseCards.map((card) => (
              <button
                key={card.id}
                type="button"
                className="btn"
                style={{ textAlign: 'left', display: 'block', height: 'auto', padding: 14 }}
                onClick={() => handleUsecaseSelect(card.id)}
                disabled={installing}
              >
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{card.vertical}</div>
                <strong style={{ display: 'block', marginBottom: 6 }}>{card.title}</strong>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>{card.one_liner}</div>
                <div style={{ fontSize: 11, color: 'var(--accent)' }}>{card.metric}</div>
                {card.persona?.snippets?.[0] && (
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 8, fontStyle: 'italic', lineHeight: 1.4 }}>
                    «{card.persona.snippets[0].text.slice(0, 100)}…»
                  </div>
                )}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
            <button type="button" className="btn" onClick={() => setStep(3)} disabled={installing}>
              {t('onboarding.skipUsecase')}
            </button>
            {installedWfId && (
              <button type="button" className="btn" onClick={() => navigate(`/workflows/${installedWfId}`)}>
                {t('onboarding.openInstalled')}
              </button>
            )}
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>{t('onboarding.workspaceTitle')}</h2>
          {teams.length > 0 ? (
            <>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
                {t('onboarding.workspaceIn')} <strong>{teams[0].name}</strong>
              </p>
              <button type="button" className="btn btn-primary" onClick={() => setStep(4)}>{t('common.continue')}</button>
            </>
          ) : (
            <>
              <input className="input" placeholder={t('onboarding.teamName')} value={teamName} onChange={(e) => setTeamName(e.target.value)} style={{ marginBottom: 12 }} />
              <button type="button" className="btn btn-primary" onClick={handleCreateTeam}>{t('onboarding.createTeam')}</button>
            </>
          )}
        </div>
      )}

      {step === 4 && (
        <div className="card">
          <h2 style={{ fontSize: 16, marginBottom: 12 }}>{t('onboarding.integrationsTitle')}</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 16 }}>{t('onboarding.integrationsDesc')}</p>
          <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
            {integrations.filter((i) => i.fields.length > 0 || i.auth_method === 'oauth').map((integ) => {
              const draft = drafts[integ.provider] || {};
              return (
                <div key={integ.provider} style={{ border: '1px solid var(--border)', borderRadius: 8, padding: 12, background: 'var(--bg)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <strong style={{ fontSize: 13 }}>{integ.name}</strong>
                    <span style={{ fontSize: 10, color: integ.configured ? 'var(--success)' : 'var(--text-muted)' }}>
                      {integ.configured ? t('common.connected') : t('common.notConnected')}
                    </span>
                  </div>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>{integ.description}</p>
                  {integ.auth_method === 'oauth' ? (
                    <button type="button" className="btn" onClick={() => handleConnectOAuth(integ.provider)} style={{ width: '100%' }}>
                      {integ.configured ? t('onboarding.reauthorize') : t('common.connect')}
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
                        <button type="button" className="btn btn-primary" onClick={() => handleSaveApiKey(integ)} style={{ flex: 1 }}>{t('common.save')}</button>
                        {integ.configured && (
                          <button type="button" className="btn" onClick={() => handleTest(integ.provider)} disabled={testing === integ.provider}>
                            {testing === integ.provider ? '…' : t('common.test')}
                          </button>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
            <button type="button" className="btn btn-primary" onClick={finish}>{t('onboarding.goToDashboard')}</button>
            <button type="button" className="btn" onClick={finish}>{t('onboarding.skipIntegrations')}</button>
          </div>
        </div>
      )}
    </div>
  );
}
