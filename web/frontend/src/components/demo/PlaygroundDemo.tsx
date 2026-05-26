import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startDemoRun } from '../../api/appClient';
import { getRun } from '../../api/workflowClient';
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
  onComplete?: (result: PlaygroundDemoResult) => void;
  onContinue?: () => void;
  showContinue?: boolean;
}

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

/** Inline Competitor Intelligence playground — auth demo run with mock fallback. */
export default function PlaygroundDemo({
  variant = 'inline',
  presets = DEFAULT_DEMO_PRESETS,
  onComplete,
  onContinue,
  showContinue = false,
}: PlaygroundDemoProps) {
  const navigate = useNavigate();
  const [target, setTarget] = useState(presets[0]?.target ?? 'Notion');
  const [ourCompany, setOurCompany] = useState(presets[0]?.our_company ?? 'Linear');
  const [activePreset, setActivePreset] = useState(presets[0]?.id ?? '');
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
      onComplete?.({
        workflow_id: demoRun.workflow_id,
        run_id: demoRun.run_id,
        mode: demoRun.mode,
        status: demoRun.status,
        artifact_url: demoRun.artifact_url,
      });
    }
    return undefined;
  }, [demoRun?.status, demoRun, clearPoll, onComplete]);

  useEffect(() => {
    if (!demoRun || demoRun.status !== 'running') return undefined;
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
  }, [demoRun?.run_id, demoRun?.status, demoRun?.workflow_id, clearPoll]);

  const handlePreset = (preset: DemoPreset) => {
    setActivePreset(preset.id);
    setTarget(preset.target);
    setOurCompany(preset.our_company);
  };

  const handleRun = async () => {
    setStarting(true);
    setError(null);
    clearPoll();
    try {
      const result = await startDemoRun(
        target.trim() || 'Notion',
        ourCompany.trim() || 'Linear',
        false,
        'competitor',
      );
      setDemoRun({
        workflow_id: result.workflow_id,
        run_id: result.run_id,
        mode: result.mode,
        artifact_url: result.artifact_url,
        logs: [],
        status: 'running',
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : t('onboarding.demoFailed'));
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
          <FeatureTag status="mock" label={t('playground.previewNote')} />
        </div>
      )}

      {!demoRun && (
        <>
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
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('demo.targetCompany')}</label>
              <input className="input" value={target} onChange={(e) => setTarget(e.target.value)} />
            </div>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('demo.ourCompany')}</label>
              <input className="input" value={ourCompany} onChange={(e) => setOurCompany(e.target.value)} />
            </div>
            <button type="button" className="btn btn-primary" onClick={handleRun} disabled={starting}>
              {starting ? t('demo.starting') : t('playground.run')}
            </button>
          </div>
        </>
      )}

      {error && (
        <div className="playground-error" role="alert">{error}</div>
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
              <button
                type="button"
                className="btn"
                onClick={() => navigate(`/workflows/${demoRun.workflow_id}?run=${demoRun.run_id}&demo=${demoRun.mode}`)}
              >
                {t('onboarding.openInBuilder')}
              </button>
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
