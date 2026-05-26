import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startDemoRun } from '../api/appClient';
import FeatureTag from '../components/ui/FeatureTag';
import { t } from '../i18n';

interface DemoModalProps {
  open: boolean;
  onClose: () => void;
}

export default function DemoModal({ open, onClose }: DemoModalProps) {
  const navigate = useNavigate();
  const [target, setTarget] = useState('Notion');
  const [ourCompany, setOurCompany] = useState('Linear');
  const [preset, setPreset] = useState<'competitor' | 'beauty' | 'lead'>('competitor');
  const [real, setReal] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    try {
      const result = await startDemoRun(
        target.trim() || 'Notion',
        ourCompany.trim() || 'Linear',
        real,
        preset,
      );
      navigate(`/workflows/${result.workflow_id}?run=${result.run_id}&demo=${result.mode}`);
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : t('demo.failed'));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(13,17,23,0.78)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-secondary)', border: '1px solid var(--border)',
          borderRadius: 12, padding: 28, width: 'min(520px, 92vw)',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 6 }}>
          <h2 style={{ fontSize: 20, margin: 0, color: 'var(--text)' }}>{t('demo.title')}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('common.close')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: 22, cursor: 'pointer', lineHeight: 1 }}
          >
            ×
          </button>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6, marginBottom: 20 }}>
          {t('demo.desc')}
        </p>

        <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
          {t('demo.preset')}
        </label>
        <select
          className="input"
          value={preset}
          onChange={(e) => setPreset(e.target.value as typeof preset)}
          style={{ marginBottom: 12 }}
        >
          <option value="competitor">{t('demo.presetCompetitor')}</option>
          <option value="beauty">{t('demo.presetBeauty')}</option>
          <option value="lead">{t('demo.presetLead')}</option>
        </select>

        {preset === 'competitor' && (
          <>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
              {t('demo.targetCompany')}
            </label>
            <input
              className="input"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="Notion"
              style={{ marginBottom: 12 }}
            />
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
              {t('demo.ourCompany')}
            </label>
            <input
              className="input"
              value={ourCompany}
              onChange={(e) => setOurCompany(e.target.value)}
              placeholder="Linear"
              style={{ marginBottom: 16 }}
            />
          </>
        )}

        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text-muted)', marginBottom: 20, cursor: 'pointer' }}>
          <input type="checkbox" checked={real} onChange={(e) => setReal(e.target.checked)} />
          {t('demo.realRun')}
        </label>

        {error && (
          <div style={{ background: 'rgba(248,81,73,0.12)', border: '1px solid rgba(248,81,73,0.4)', color: '#f85149', padding: 10, borderRadius: 6, marginBottom: 12, fontSize: 13 }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button type="button" className="btn" onClick={onClose} disabled={running}>
            {t('common.cancel')}
          </button>
          <button type="button" className="btn btn-primary" onClick={handleRun} disabled={running}>
            {running ? t('demo.starting') : t('demo.run')}
          </button>
        </div>

        <p style={{ fontSize: 11, color: 'var(--text-subtle)', marginTop: 16, marginBottom: 0, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <FeatureTag status="mock" showDot={false} />
          {t('demo.fallbackNote')}
        </p>
      </div>
    </div>
  );
}
