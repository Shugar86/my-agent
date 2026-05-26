import PlaygroundDemo from '../components/demo/PlaygroundDemo';
import FeatureTag from '../components/ui/FeatureTag';
import { loginUrl } from '../lib/routes';
import { t } from '../i18n';

/** Public live demo at `/demo` — no auth required. */
export default function PublicDemoPage() {
  return (
    <div className="landing-section" style={{ maxWidth: 960 }}>
      <div className="landing-section-header">
        <span className="landing-section-tag">{t('landing.liveDemoTag')}</span>
        <h1 className="landing-section-title">{t('demoPage.title')}</h1>
        <p className="landing-section-desc">{t('demoPage.subtitle')}</p>
        <FeatureTag status="mock" label={t('featureTag.preview')} reason={t('playground.previewModeReason')} showDot={false} />
      </div>
      <div className="landing-demo-embed">
        <PlaygroundDemo publicMode showAdvancedPresets />
      </div>
      <p style={{ textAlign: 'center', marginTop: 24, fontSize: 14, color: 'var(--landing-text-muted)' }}>
        <a href={loginUrl('/app/onboarding')} className="landing-btn landing-btn-primary">
          {t('landing.saveWorkflowCta')}
        </a>
      </p>
    </div>
  );
}
