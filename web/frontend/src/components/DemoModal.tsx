import PlaygroundDemo from './demo/PlaygroundDemo';
import { t } from '../i18n';

interface DemoModalProps {
  open: boolean;
  onClose: () => void;
}

/** Modal wrapper around PlaygroundDemo — same presets and real-run toggle as dashboard. */
export default function DemoModal({ open, onClose }: DemoModalProps) {
  if (!open) return null;

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
          borderRadius: 12, padding: 28, width: 'min(560px, 92vw)', maxHeight: '90vh',
          overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 12 }}>
          <div>
            <h2 style={{ fontSize: 20, margin: 0, color: 'var(--text)' }}>{t('demo.title')}</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 6, marginBottom: 0 }}>
              {t('demo.desc')}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t('common.close')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: 22, cursor: 'pointer', lineHeight: 1 }}
          >
            ×
          </button>
        </div>
        <PlaygroundDemo
          variant="compact"
          showAdvancedPresets
          navigateOnComplete
          onComplete={onClose}
        />
      </div>
    </div>
  );
}
