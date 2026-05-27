import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDemoSample, startDemoRun, startPublicDemoRun, getPublicDemoRun } from '../../api/appClient';
import { getRun } from '../../api/workflowClient';
import {
  advanceOfflineDemoRun,
  buildOfflineDemoRun,
  OFFLINE_DEMO_STEP_MS,
} from '../../lib/offlineDemo';
import FeatureTag from '../ui/FeatureTag';
import { getPageFeatureStatus } from '../../config/featureRegistry';
import DemoStepper from './DemoStepper';
import {
  DEFAULT_DEMO_NODE_ORDER,
  DEFAULT_DEMO_PRESETS,
  type DemoPreset,
} from '../../lib/demoNodeLabels';
import { appRoute, loginUrl } from '../../lib/routes';
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

interface DemoMetrics {
  tokens: number;
  costUsd: number;
  durationHuman: string;
}

interface PlaygroundDemoProps {
  variant?: 'inline' | 'compact';
  presets?: DemoPreset[];
  showAdvancedPresets?: boolean;
  lockPreset?: 'competitor' | 'beauty' | 'lead';
  publicMode?: boolean;
  onComplete?: (result: PlaygroundDemoResult) => void;
  onContinue?: () => void;
  showContinue?: boolean;
  navigateOnComplete?: boolean;
}

const DEFAULT_METRICS: DemoMetrics = {
  tokens: 18420,
  costUsd: 0.42,
  durationHuman: '~4h saved',
};

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

/** Inline Competitor Intelligence playground — auth demo run with mock/offline fallback. */
export default function PlaygroundDemo({
  variant = 'inline',
  presets = DEFAULT_DEMO_PRESETS,
  showAdvancedPresets = false,
  lockPreset,
  publicMode = false,
  onComplete,
  onContinue,
  showContinue = false,
  navigateOnComplete = false,
}: PlaygroundDemoProps) {
  const navigate = useNavigate();
  const [target, setTarget] = useState(presets[0]?.target ?? 'Notion');
  const [ourCompany, setOurCompany] = useState(presets[0]?.our_company ?? 'Linear');
  const [activePreset, setActivePreset] = useState(presets[0]?.id ?? '');
  const [demoPreset, setDemoPreset] = useState<'competitor' | 'beauty' | 'lead'>(lockPreset ?? 'competitor');
  const [nodeOrder, setNodeOrder] = useState<string[]>(DEFAULT_DEMO_NODE_ORDER);
  const [realRun, setRealRun] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offlineNotice, setOfflineNotice] = useState(false);
  const [demoRun, setDemoRun] = useState<DemoRunState | null>(null);
  const [metrics, setMetrics] = useState<DemoMetrics>(DEFAULT_METRICS);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const offlineTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const completedRunIdRef = useRef<string | null>(null);

  const clearPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const clearOfflineTimer = useCallback(() => {
    if (offlineTimerRef.current) {
      clearInterval(offlineTimerRef.current);
      offlineTimerRef.current = null;
    }
  }, []);

  useEffect(() => () => {
    clearPoll();
    clearOfflineTimer();
  }, [clearPoll, clearOfflineTimer]);

  useEffect(() => {
    getDemoSample(lockPreset ?? demoPreset)
      .then((sample) => {
        if (sample.node_order?.length) {
          setNodeOrder(sample.node_order);
        }
        const summary = sample.summary as Record<string, unknown>;
        setMetrics({
          tokens: Number(summary.tokens_used ?? DEFAULT_METRICS.tokens),
          costUsd: Number(summary.estimated_cost_usd ?? DEFAULT_METRICS.costUsd),
          durationHuman: String(summary.total_duration_human ?? DEFAULT_METRICS.durationHuman),
        });
      })
      .catch(() => setMetrics(DEFAULT_METRICS));
  }, [lockPreset, demoPreset]);

  useEffect(() => {
    if (!demoRun || demoRun.status === 'running') return undefined;
    if (completedRunIdRef.current === demoRun.run_id) return undefined;
    clearPoll();
    if (demoRun.status === 'success' || demoRun.status === 'failed') {
      completedRunIdRef.current = demoRun.run_id;
      const result: PlaygroundDemoResult = {
        workflow_id: demoRun.workflow_id,
        run_id: demoRun.run_id,
        mode: demoRun.mode,
        status: demoRun.status,
        artifact_url: demoRun.artifact_url,
      };
      onComplete?.(result);
      if (navigateOnComplete && !demoRun.offline && demoRun.status === 'success') {
        navigate(appRoute(`/workflows/${demoRun.workflow_id}?run=${demoRun.run_id}&demo=${demoRun.mode}`));
      }
    }
    return undefined;
  }, [demoRun?.status, demoRun, clearPoll, onComplete, navigateOnComplete, navigate]);

  useEffect(() => {
    if (!demoRun || demoRun.status !== 'running' || demoRun.offline) return undefined;
    pollRef.current = setInterval(async () => {
      try {
        const run = publicMode
          ? await getPublicDemoRun(demoRun.run_id, demoPreset)
          : await getRun(demoRun.workflow_id, demoRun.run_id);
        setDemoRun((prev) =>
          prev
            ? {
                ...prev,
                logs: run.logs || [],
                status: run.status,
              }
            : prev,
        );
        if (publicMode && 'node_order' in run && run.node_order?.length) {
          setNodeOrder(run.node_order);
        }
      } catch {
        clearPoll();
        setError(t('playground.pollError'));
      }
    }, 500);
    return () => clearPoll();
  }, [demoRun?.run_id, demoRun?.status, demoRun?.workflow_id, demoRun?.offline, clearPoll, publicMode, demoPreset]);

  useEffect(() => {
    if (!demoRun?.offline || demoRun.status !== 'running') return undefined;
    clearOfflineTimer();
    offlineTimerRef.current = setInterval(() => {
      setDemoRun((prev) => {
        if (!prev?.offline || prev.status !== 'running') return prev;
        const advanced = advanceOfflineDemoRun(
          {
            workflow_id: prev.workflow_id,
            run_id: prev.run_id,
            mode: 'mock',
            artifact_url: prev.artifact_url || '',
            logs: prev.logs,
            status: 'running',
            node_order: nodeOrder,
          },
          target.trim() || 'Notion',
          ourCompany.trim() || 'Linear',
          demoPreset,
        );
        return { ...prev, logs: advanced.logs, status: advanced.status };
      });
    }, OFFLINE_DEMO_STEP_MS);
    return () => clearOfflineTimer();
  }, [demoRun?.run_id, demoRun?.offline, demoRun?.status, target, ourCompany, demoPreset, clearOfflineTimer, nodeOrder]);

  const handlePreset = (preset: DemoPreset) => {
    setActivePreset(preset.id);
    setTarget(preset.target);
    setOurCompany(preset.our_company);
  };

  const applyOfflineRun = () => {
    const offline = buildOfflineDemoRun(
      target.trim() || 'Notion',
      ourCompany.trim() || 'Linear',
      lockPreset ?? demoPreset,
      { animate: true, nodeOrder },
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
    completedRunIdRef.current = null;
    clearPoll();
    clearOfflineTimer();
    try {
      const result = publicMode
        ? await startPublicDemoRun(
            target.trim() || 'Notion',
            ourCompany.trim() || 'Linear',
            lockPreset ?? demoPreset,
          )
        : await startDemoRun(
            target.trim() || 'Notion',
            ourCompany.trim() || 'Linear',
            realRun,
            lockPreset ?? demoPreset,
          );
      if (result.node_order?.length) {
        setNodeOrder(result.node_order);
      }
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

  const handleRunAgain = () => {
    completedRunIdRef.current = null;
    clearPoll();
    clearOfflineTimer();
    setDemoRun(null);
    setError(null);
    setOfflineNotice(false);
  };

  const isCompact = variant === 'compact';
  const isRunning = demoRun?.status === 'running';
  const isDone = demoRun && demoRun.status !== 'running';
  const statusTag = demoRun?.offline || demoRun?.mode === 'mock' ? 'mock' : 'live';
  const showPreviewBanner = offlineNotice || (demoRun && (demoRun.offline || demoRun.mode === 'mock')) || publicMode;

  return (
    <section className={`playground-demo ${isCompact ? 'playground-demo--compact' : ''}`}>
      {showPreviewBanner && !demoRun && (
        <div className="demo-preview-banner" role="status">
          <FeatureTag status="mock" reason={t('playground.previewModeReason')} showDot={false} />
          <span>{t('playground.previewModeBanner')}</span>
        </div>
      )}
      {!isCompact && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, margin: 0 }}>{t('playground.title')}</h2>
          <FeatureTag status="beta" label={t('playground.readyToRun')} showDot={false} />
        </div>
      )}

      {!demoRun && (
        <>
          {showAdvancedPresets && !lockPreset && (
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
            {showAdvancedPresets && !lockPreset && (
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
        <div className="demo-preview-banner" role="status">
          <FeatureTag status={getPageFeatureStatus('playground.offline')} reason={t('playground.previewModeReason')} showDot={false} />
          <span>{t('playground.offlineNotice')}</span>
        </div>
      )}

      {demoRun && (
        <div className="card" style={{ marginTop: isCompact ? 0 : 16, padding: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
            <FeatureTag status={statusTag} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              {isRunning ? t('playground.running') : demoRun.status}
            </span>
          </div>

          {isRunning && demoRun.logs.length === 0 && (
            <div className="skeleton" style={{ height: 120, marginBottom: 12 }} />
          )}

          {(isRunning || isDone) && demoRun.logs.length > 0 && (
            <DemoStepper
              nodeOrder={nodeOrder}
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
              {!demoRun.offline && !publicMode && (
                <button
                  type="button"
                  className="btn"
                  onClick={() => navigate(appRoute(`/workflows/${demoRun.workflow_id}?run=${demoRun.run_id}&demo=${demoRun.mode}`))}
                >
                  {t('onboarding.openInBuilder')}
                </button>
              )}
              {publicMode && isDone && demoRun.status === 'success' && (
                <a href={loginUrl('/app/onboarding')} className="btn btn-primary">
                  {t('landing.saveWorkflowCta')}
                </a>
              )}
              <button type="button" className="btn btn-ghost" onClick={handleRunAgain}>
                {t('playground.runAgain')}
              </button>
            </div>
          )}

          {isDone && (
            <p style={{ fontSize: 11, color: 'var(--text-subtle)', marginTop: 12, marginBottom: 0 }}>
              {t('demo.fallbackNote')} · {formatTokens(metrics.tokens)} tokens · ~${metrics.costUsd.toFixed(2)} · {metrics.durationHuman}
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
