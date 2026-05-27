import { Link } from 'react-router-dom';
import PlaygroundDemo from '../components/demo/PlaygroundDemo';
import ProductNarrative from '../components/ProductNarrative';
import TemplateCardGrid from '../components/marketplace/TemplateCardGrid';
import FeatureTag from '../components/ui/FeatureTag';
import { getPageFeatureStatus } from '../config/featureRegistry';
import { COMPETITOR_DEMO_PRESETS } from '../lib/demoNodeLabels';
import { loginUrl } from '../lib/routes';
import { t } from '../i18n';

const PROOF_ITEMS = [
  'Mary Jewelry — Telegram-консультант',
  'DocBrain — legal SaaS, Stripe',
  'Pretenzia — 15 000+ документов',
  'PEGAS Touristik — автоканал',
];

const PROBLEM_ICONS = ['⏱', '🔗', '💬'];

/** Public marketing landing at `/`. */
export default function LandingPage() {
  return (
    <>
      <header className="landing-hero">
        <div className="landing-hero-grid">
          <div>
            <div className="landing-hero-pretitle">
              <span className="status-dot" />
              <span>{t('landing.pretitle')}</span>
            </div>
            <h1 className="landing-hero-title">
              {t('landing.heroTitleLine1')}
              <br />
              {t('landing.heroTitleLine2Prefix')}{' '}
              <span className="accent">{t('landing.heroTitleAccent')}</span>
            </h1>
            <p className="landing-hero-desc">{t('landing.heroDesc')}</p>
            <div className="landing-hero-actions">
              <Link to="/showcase#playground" className="landing-btn landing-btn-primary">
                {t('landing.heroPrimaryCta')}
              </Link>
              <Link to="/showcase" className="landing-btn landing-btn-secondary">
                {t('landing.heroSecondaryCta')}
              </Link>
            </div>
            <div className="landing-hero-stats" style={{ position: 'relative' }}>
              <FeatureTag status={getPageFeatureStatus('landing.heroStats')} showDot={false} />
              <div>
                <span className="landing-stat-value">50+</span>
                <span className="landing-stat-label">{t('landing.statTemplates')}</span>
              </div>
              <div>
                <span className="landing-stat-value">90 {t('landing.statSec')}</span>
                <span className="landing-stat-label">{t('landing.statTimeToWow')}</span>
              </div>
              <div>
                <span className="landing-stat-value">$0.42</span>
                <span className="landing-stat-label">{t('landing.statDemoCost')}</span>
              </div>
              <div>
                <span className="landing-stat-value">~4ч</span>
                <span className="landing-stat-label">{t('landing.statSaved')}</span>
              </div>
            </div>
          </div>
          <div className="landing-device-frame">
            <div className="landing-device-frame__bar">
              <span className="landing-device-frame__dot" />
              <span className="landing-device-frame__dot" />
              <span className="landing-device-frame__dot" />
            </div>
            <div className="landing-device-frame__body">
              <img src="/welcome-assets/assets/product-dashboard.svg" alt={t('landing.productScreenshotAlt')} />
            </div>
          </div>
        </div>
      </header>

      <div className="landing-proof-strip">
        <div className="landing-proof-inner">
          {PROOF_ITEMS.map((item, i) => (
            <span key={item}>
              {i > 0 && ' · '}
              {item}
            </span>
          ))}
        </div>
      </div>

      <section id="problems" className="landing-section">
        <div className="landing-section-header">
          <span className="landing-section-tag">{t('landing.problemsTag')}</span>
          <h2 className="landing-section-title">{t('landing.problemsTitle')}</h2>
        </div>
        <div className="landing-cards-grid">
          <article className="landing-card">
            <div className="landing-card-num">{PROBLEM_ICONS[0]}</div>
            <h3>{t('landing.problem1Title')}</h3>
            <p>{t('landing.problem1Desc')}</p>
          </article>
          <article className="landing-card">
            <div className="landing-card-num">{PROBLEM_ICONS[1]}</div>
            <h3>{t('landing.problem2Title')}</h3>
            <p>{t('landing.problem2Desc')}</p>
          </article>
          <article className="landing-card">
            <div className="landing-card-num">{PROBLEM_ICONS[2]}</div>
            <h3>{t('landing.problem3Title')}</h3>
            <p>{t('landing.problem3Desc')}</p>
          </article>
        </div>
      </section>

      <section id="product" className="landing-section">
        <div className="landing-section-header">
          <span className="landing-section-tag">{t('landing.howTag')}</span>
          <h2 className="landing-section-title">{t('landing.howTitle')}</h2>
          <p className="landing-section-desc">{t('landing.howDesc')}</p>
        </div>
        <div style={{ marginBottom: 32 }}>
          <ProductNarrative variant="steps" />
        </div>
        <div className="landing-cards-grid">
          <article className="landing-card">
            <div className="landing-card-num">1</div>
            <h3>{t('landing.how1Title')}</h3>
            <p>{t('landing.how1Desc')}</p>
          </article>
          <article className="landing-card">
            <div className="landing-card-num">2</div>
            <h3>{t('landing.how2Title')}</h3>
            <p>{t('landing.how2Desc')}</p>
          </article>
          <article className="landing-card">
            <div className="landing-card-num">3</div>
            <h3>{t('landing.how3Title')}</h3>
            <p>{t('landing.how3Desc')}</p>
          </article>
        </div>
      </section>

      <section id="live-demo" className="landing-section">
        <div className="landing-section-header">
          <span className="landing-section-tag">{t('landing.liveDemoTag')}</span>
          <FeatureTag status={getPageFeatureStatus('landing.liveDemo')} showDot={false} />
          <h2 className="landing-section-title">{t('landing.liveDemoTitle')}</h2>
          <p className="landing-section-desc">{t('landing.liveDemoDesc')}</p>
        </div>
        <div className="landing-demo-embed">
          <PlaygroundDemo variant="compact" publicMode lockPreset="competitor" presets={COMPETITOR_DEMO_PRESETS} />
        </div>
      </section>

      <section className="landing-section">
        <div className="landing-section-header">
          <span className="landing-section-tag">{t('landing.trustTag')}</span>
          <h2 className="landing-section-title">{t('landing.trustTitle')}</h2>
        </div>
        <div className="landing-cards-grid">
          <article className="landing-card">
            <h3>{t('landing.trust1Title')}</h3>
            <p>{t('landing.trust1Desc')}</p>
          </article>
          <article className="landing-card">
            <h3>{t('landing.trust2Title')}</h3>
            <p>{t('landing.trust2Desc')}</p>
          </article>
          <article className="landing-card">
            <h3>{t('landing.trust3Title')}</h3>
            <p>{t('landing.trust3Desc')}</p>
          </article>
        </div>
      </section>

      <section id="marketplace-preview" className="landing-section">
        <div className="landing-section-header">
          <span className="landing-section-tag">{t('landing.marketplaceTag')}</span>
          <h2 className="landing-section-title">{t('landing.marketplaceTitle')}</h2>
          <p className="landing-section-desc">{t('landing.marketplaceDesc')}</p>
        </div>
        <TemplateCardGrid limit={4} publicMode />
        <div style={{ textAlign: 'center', marginTop: 28 }}>
          <a href={loginUrl('/app/marketplace')} className="landing-btn landing-btn-primary">
            {t('landing.marketplaceCta')}
          </a>
        </div>
      </section>

      <section id="pricing" className="landing-section">
        <div className="landing-section-header">
          <span className="landing-section-tag">{t('landing.pricingTag')}</span>
          <h2 className="landing-section-title">{t('landing.pricingTitle')}</h2>
        </div>
        <div className="landing-pricing-grid">
          <div className="landing-pricing-card">
            <h3>Starter</h3>
            <div className="landing-pricing-price">$0 <span>/ {t('landing.pricingPerMonth')}</span></div>
            <ul>
              <li>{t('landing.pricingStarter1')}</li>
              <li>{t('landing.pricingStarter2')}</li>
              <li>{t('landing.pricingStarter3')}</li>
            </ul>
            <a href={loginUrl()} className="landing-btn landing-btn-secondary" style={{ width: '100%' }}>
              {t('landing.pricingStart')}
            </a>
          </div>
          <div className="landing-pricing-card landing-pricing-card--featured">
            <span className="landing-pricing-badge">{t('landing.pricingPopular')}</span>
            <h3>Pro</h3>
            <div className="landing-pricing-price">$49 <span>/ {t('landing.pricingPerMonth')}</span></div>
            <ul>
              <li>{t('landing.pricingPro1')}</li>
              <li>{t('landing.pricingPro2')}</li>
              <li>{t('landing.pricingPro3')}</li>
              <li>{t('landing.pricingPro4')}</li>
            </ul>
            <a href={loginUrl()} className="landing-btn landing-btn-primary" style={{ width: '100%' }}>
              {t('landing.pricingTryPro')}
            </a>
          </div>
          <div className="landing-pricing-card">
            <h3>Enterprise</h3>
            <div className="landing-pricing-price">Custom</div>
            <ul>
              <li>{t('landing.pricingEnt1')}</li>
              <li>{t('landing.pricingEnt2')}</li>
              <li>{t('landing.pricingEnt3')}</li>
            </ul>
            <Link to="/showcase#cta" className="landing-btn landing-btn-secondary" style={{ width: '100%' }}>
              {t('landing.pricingContact')}
            </Link>
          </div>
        </div>
      </section>

      <section className="landing-footer-cta">
        <h2>{t('landing.footerCtaTitle')}</h2>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/showcase#playground" className="landing-btn landing-btn-primary">{t('landing.footerCtaDemo')}</Link>
          <Link to="/showcase" className="landing-btn landing-btn-secondary">{t('landing.footerCtaCases')}</Link>
        </div>
      </section>

      <footer className="landing-site-footer">
        <div className="landing-footer-inner">
          <Link to="/" className="landing-brand">
            <BrandLogo />
            <span>{t('app.title')}</span>
          </Link>
          <div className="landing-footer-links">
            <Link to="/showcase">{t('nav.showcase')}</Link>
            <Link to="/showcase#playground">{t('landing.navDemo')}</Link>
            <a href="/#pricing">{t('landing.navPricing')}</a>
            <a href={loginUrl()}>{t('landing.navLogin')}</a>
          </div>
          <p style={{ fontSize: 12, color: 'var(--landing-text-muted)', margin: 0 }}>
            {t('landing.footerCopy')}
          </p>
        </div>
      </footer>
    </>
  );
}

function BrandLogo() {
  return (
    <svg viewBox="0 0 40 40" fill="none" width={28} height={28} aria-hidden>
      <circle cx="20" cy="20" r="18" stroke="currentColor" strokeWidth="3" />
      <circle cx="20" cy="20" r="7" fill="currentColor" />
    </svg>
  );
}
