import { t } from '../i18n';

interface ProductNarrativeProps {
  variant: 'strip' | 'steps';
  context?: 'landing' | 'app';
  className?: string;
}

const STEP_KEYS = ['narrative.template', 'narrative.workflow', 'narrative.result'] as const;
const STEP_ICONS = ['📦', '⚡', '📄'];

/** Glue narrative: Template → Workflow → Result. */
export default function ProductNarrative({ variant, context = 'app', className = '' }: ProductNarrativeProps) {
  if (variant === 'strip') {
    const stripClass = context === 'landing' ? 'landing-narrative-strip' : 'app-narrative-strip';
    return (
      <div className={`${stripClass} ${className}`.trim()} role="note">
        <strong>{t('narrative.template')}</strong>
        {' → '}
        <strong>{t('narrative.workflow')}</strong>
        {' → '}
        <strong>{t('narrative.result')}</strong>
      </div>
    );
  }

  return (
    <div
      className={className}
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: 16,
        textAlign: 'center',
      }}
    >
      {STEP_KEYS.map((key, i) => (
        <div key={key}>
          <div style={{ fontSize: 28, marginBottom: 8 }}>{STEP_ICONS[i]}</div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>{t(key)}</div>
        </div>
      ))}
    </div>
  );
}
