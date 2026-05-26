import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startDemoRun } from '../../api/appClient';
import { getRun } from '../../api/workflowClient';
import { buildOfflineDemoRun } from '../../lib/offlineDemo';
import FeatureTag from '../ui/FeatureTag';
import DemoStepper from './DemoStepper';
import {
  DEFAULT_DEMO_NODE_ORDER,
  DEFAULT_DEMO_PRESETS,
  type DemoPreset,
} from '../../lib/demoNodeLabels';
import { t } from '../../i18n';

interface DemoRunState {
  workflow_id: string;
  run_id: string;
  mode: 'mock' | 'real';
  artifact_url?: string;
  logs: Array<{ node_id: string; event: string; detail?: unknown }>;
  status: string;
  offline?: boolean;
}

export interface PlaygroundDemoResult {
  workflow_id: string;
  run_id: string;
  mode: 'mock' | 'real';
  status: string;
  artifact_url?: string;
}

interface PlaygroundDemoProps {
  variant?: 'inline' | 'compact';
  presets?: DemoPreset[];
  showAdvancedPresets?: boolean;
  onComplete?: (result: PlaygroundDemoResult) => void;
  onContinue?: () => void;
  showContinue?: boolean;
  navigateOnComplete?: boolean;
}

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

/** Inline Competitor Intelligence playground — auth demo run with mock/offline fallback. */
export default function PlaygroundDemo({
  variant = 'inline',
  presets = DEFAULT_DEMO_PRESETS,
  showAdvancedPresets = false,
  onComplete,
  onContinue,
  showContinue = false,
  navigateOnComplete = false,
}: PlaygroundDemoProps) {
  const navigate = useNavigate();
  const [target, setTarget] = useState(presets[0]?.target ?? 'Notion');
  const [ourCompany, setOurCompany] = useState(presets[0]?.our_company ?? 'Linear');
  const [activePreset, setActivePreset] = useState(presets[0]?.id ?? '');
  const [demoPreset, setDemoPreset] = useState<'competitor' | 'beauty' | 'lead'>('competitor');
  const [realRun, setRealRun] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offlineNotice, setOfflineNotice] = useState(false);
  const [demoRun, setDemoRun] = useState<DemoRunState | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => () => clearPoll(), [clearPoll]);

  useEffect(() => {
    if (!demoRun || demoRun.status === 'running') return undefined;
    clearPoll();
    if (demoRun.status === 'success' || demoRun.status === 'failed') {
      const result: PlaygroundDemoResult = {
        workflow_id: demoRun.workflow_id,
        run_id: demoRun.run_id,
        mode: demoRun.mode,
        status: demoRun.status,
        artifact_url: demoRun.artifact_url,
      };
      onComplete?.(result);
      if (navigateOnComplete && !demoRun.offline && demoRun.status === 'success') {
        navigate(`/workflows/${demoRun.workflow_id}?run=${demoRun.run_id}&demo=${demoRun.mode}`);
      }
    }
    return undefined;
  }, [demoRun?.status, demoRun, clearPoll, onComplete, navigateOnComplete, navigate]);

  useEffect(() => {
    if (!demoRun || demoRun.status !== 'running' || demoRun.offline) return undefined;
    pollRef.current = setInterval(async () => {
      try {
        const run = await getRun(demoRun.workflow_id, demoRun.run_id);
        setDemoRun((prev) =>
          prev
            ? {
                ...prev,
                logs: run.logs || [],
                status: run.status,
              }
            : prev,
        );
      } catch {
        clearPoll();
        setError(t('playground.pollError'));
      }
    }, 500);
    return () => clearPoll();
  }, [demoRun?.run_id, demoRun?.status, demoRun?.workflow_id, demoRun?.offline, clearPoll]);

  const handlePreset = (preset: DemoPreset) => {
    setActivePreset(preset.id);
    setTarget(preset.target);
    setOurCompany(preset.our_company);
  };

  const applyOfflineRun = () => {
    const offline = buildOfflineDemoRun(
      target.trim() || 'Notion',
      ourCompany.trim() || 'Linear',
      demoPreset,
    );
    setOfflineNotice(true);
    setDemoRun({
      workflow_id: offline.workflow_id,
      run_id: offline.run_id,
      mode: offline.mode,
      artifact_url: offline.artifact_url,
      logs: offline.logs,
      status: offline.status,
      offline: true,
    });
  };

  const handleRun = async () => {
    setStarting(true);
    setError(null);
    setOfflineNotice(false);
    clearPoll();
    try {
      const result = await startDemoRun(
        target.trim() || 'Notion',
        ourCompany.trim() || 'Linear',
        realRun,
        demoPreset,
      );
      setDemoRun({
        workflow_id: result.workflow_id,
        run_id: result.run_id,
        mode: result.mode,
        artifact_url: result.artifact_url,
        logs: [],
        status: 'running',
      });
    } catch {
      applyOfflineRun();
    } finally {
      setStarting(false);
    }
  };

  const isCompact = variant === 'compact';
  const isRunning = demoRun?.status === 'running';
  const isDone = demoRun && demoRun.status !== 'running';

  return (
    <section className={`playground-demo ${isCompact ? 'playground-demo--compact' : ''}`}>
      {!isCompact && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, margin: 0 }}>{t('playground.title')}</h2>
          <FeatureTag status="beta" label={t('playground.readyToRun')} showDot={false} />
        </div>
      )}

      {!demoRun && (
        <>
          {showAdvancedPresets && (
            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                {t('demo.preset')}
              </label>
              <select
                className="input"
                value={demoPreset}
                onChange={(e) => setDemoPreset(e.target.value as typeof demoPreset)}
                style={{ maxWidth: 320 }}
              >
                <option value="competitor">{t('demo.presetCompetitor')}</option>
                <option value="beauty">{t('demo.presetBeauty')}</option>
                <option value="lead">{t('demo.presetLead')}</option>
              </select>
            </div>
          )}
          <div className="playground-presets">
            {presets.map((p) => (
              <button
                key={p.id}
                type="button"
                className={`btn btn-sm ${activePreset === p.id ? 'btn-primary' : ''}`}
                onClick={() => handlePreset(p)}
              >
                {p.label}
              </button>
            ))}
          </div>
          <div className="playground-form" style={{ display: 'grid', gap: 12, marginTop: 12, maxWidth: 480 }}>
            {(showAdvancedPresets ? demoPreset === 'competitor' : true) && (
              <>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('demo.targetCompany')}</label>
                  <input className="input" value={target} onChange={(e) => setTarget(e.target.value)} />
                </div>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('demo.ourCompany')}</label>
                  <input className="input" value={ourCompany} onChange={(e) => setOurCompany(e.target.value)} />
                </div>
              </>
            )}
            {showAdvancedPresets && (
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text-muted)', cursor: 'pointer' }}>
                <input type="checkbox" checked={realRun} onChange={(e) => setRealRun(e.target.checked)} />
                {t('demo.realRun')}
              </label>
            )}
            <button type="button" className="btn btn-primary" onClick={handleRun} disabled={starting}>
              {starting ? t('demo.starting') : t('playground.run')}
            </button>
          </div>
        </>
      )}

      {error && (
        <div className="playground-error" role="alert">{error}</div>
      )}

      {offlineNotice && (
        <p style={{ fontSize: 12, color: 'var(--warning)', marginTop: 8 }}>{t('playground.offlineNotice')}</p>
      )}

      {demoRun && (
        <div className="card" style={{ marginTop: isCompact ? 0 : 16, padding: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
            <FeatureTag status={demoRun.mode === 'mock' ? 'mock' : 'live'} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {isRunning ? t('playground.running') : demoRun.status}
            </span>
          </div>

          {isRunning && (
            <div className="skeleton" style={{ height: 120, marginBottom: 12 }} />
          )}

          {(isRunning || isDone) && (
            <DemoStepper
              nodeOrder={DEFAULT_DEMO_NODE_ORDER}
              logs={demoRun.logs}
              status={demoRun.status}
            />
          )}

          {isDone && (
            <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
              {demoRun.artifact_url && (
                <a href={demoRun.artifact_url} className="btn btn-primary" download target="_blank" rel="noreferrer">
                  {t('onboarding.downloadDocx')}
                </a>
              )}
              {showContinue && onContinue && (
                <button type="button" className="btn btn-primary" onClick={onContinue}>
                  {t('common.continue')}
                </button>
              )}
              {!demoRun.offline && (
                <button
                  type="button"
                  className="btn"
                  onClick={() => navigate(`/workflows/${demoRun.workflow_id}?run=${demoRun.run_id}&demo=${demoRun.mode}`)}
                >
                  {t('onboarding.openInBuilder')}
                </button>
              )}
              {!isCompact && (
                <button type="button" className="btn btn-ghost" onClick={() => setDemoRun(null)}>
                  {t('playground.runAgain')}
                </button>
              )}
            </div>
          )}

          {isDone && demoRun.mode === 'mock' && (
            <p style={{ fontSize: 11, color: 'var(--text-subtle)', marginTop: 12, marginBottom: 0 }}>
              {t('demo.fallbackNote')} · {formatTokens(18420)} tokens · ~$0.42 · ~4ч saved
            </p>
          )}
        </div>
      )}

      {!isCompact && !demoRun && (
        <p style={{ fontSize: 11, color: 'var(--text-subtle)', marginTop: 12 }}>
          {t('demo.fallbackNote')}
        </p>
      )}
    </section>
  );
}
