import PlaygroundDemo from '../components/demo/PlaygroundDemo';
import FeatureTag from '../components/ui/FeatureTag';
import { getPageFeatureStatus } from '../config/featureRegistry';
import { COMPETITOR_DEMO_PRESETS } from '../lib/demoNodeLabels';
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
        <FeatureTag status={getPageFeatureStatus('showcase.playground')} label={t('featureTag.preview')} reason={t('playground.previewModeReason')} showDot={false} />
        <p className="landing-section-desc" style={{ marginTop: 8 }}>
          <a href="/showcase#playground">{t('showcase.canonicalCta')}</a>
        </p>
      </div>
      <div className="landing-demo-embed">
        <PlaygroundDemo publicMode lockPreset="competitor" presets={COMPETITOR_DEMO_PRESETS} />
      </div>
      <p style={{ textAlign: 'center', marginTop: 24, fontSize: 14, color: 'var(--landing-text-muted)' }}>
        <a href={loginUrl('/app/onboarding')} className="landing-btn landing-btn-primary">
          {t('landing.saveWorkflowCta')}
        </a>
      </p>
    </div>
  );
}
