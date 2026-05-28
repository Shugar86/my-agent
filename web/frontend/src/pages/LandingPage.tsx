import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import AgentPreviewWidget from '../components/demo/AgentPreviewWidget';
import ProductNarrative from '../components/ProductNarrative';
import TemplateCardGrid from '../components/marketplace/TemplateCardGrid';
import FeatureTag from '../components/ui/FeatureTag';
import { loginUrl } from '../lib/routes';
import { t } from '../i18n';

interface ShowcaseCard {
  id: string;
  vertical: string;
  title: string;
  one_liner: string;
  status: 'live' | 'lab';
  platform: string;
  metric: string;
  icon: string;
  persona: { snippets: Array<{ text: string }> };
}

const FEATURED_IDS = ['ararat', 'pegasszn', 'docbrain'];

/** Public marketing landing at `/`. */
export default function LandingPage() {
  const [showcaseCards, setShowcaseCards] = useState<ShowcaseCard[]>([]);

  useEffect(() => {
    fetch('/welcome-assets/data/showcase.json')
      .then((r) => r.json())
      .then((data) => {
        const cards: ShowcaseCard[] = data.cards || [];
        const featured = cards.filter((c) => FEATURED_IDS.includes(c.id) && c.status === 'live');
        setShowcaseCards(featured.length > 0 ? featured : cards.filter((c) => c.status === 'live').slice(0, 3));
      })
      .catch(() => {});
  }, []);

  return (
    <>
      {/* --- Hero: text + live AgentPreviewWidget --- */}
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
              <a href="#live-demo" className="landing-btn landing-btn-primary">
                {t('landing.heroPrimaryCta')}
              </a>
              <a href="#showcase" className="landing-btn landing-btn-secondary">
                {t('landing.heroSecondaryCta')}
              </a>
            </div>
            <div className="landing-hero-stats">
              <div>
                <span className="landing-stat-value">50+</span>
                <span className="landing-stat-label">{t('landing.statTemplates')}</span>
              </div>
              <div>
                <span className="landing-stat-value">7</span>
                <span className="landing-stat-label">{t('landing.statDeployments')}</span>
              </div>
              <div>
                <span className="landing-stat-value">30+</span>
                <span className="landing-stat-label">{t('landing.statSkills')}</span>
              </div>
              <div>
                <span className="landing-stat-value">2 {t('landing.statMin')}</span>
                <span className="landing-stat-label">{t('landing.statFirstAgent')}</span>
              </div>
            </div>
          </div>
          <div id="live-demo" className="landing-hero-widget">
            <AgentPreviewWidget />
          </div>
        </div>
      </header>

      {/* --- Showcase: 3 live cases --- */}
      <section id="showcase" className="landing-section">
        <div className="landing-section-header">
          <span className="landing-section-tag">{t('landing.showcaseTag')}</span>
          <h2 className="landing-section-title">{t('landing.showcaseTitle')}</h2>
          <p className="landing-section-desc">{t('landing.showcaseDesc')}</p>
        </div>
        {showcaseCards.length > 0 && (
          <div className="landing-cards-grid">
            {showcaseCards.map((card) => (
              <article key={card.id} className="landing-card">
                <div style={{ display: 'flex', gap: 12, marginBottom: 10 }}>
                  <img src={`/welcome-assets/assets/icons/${card.icon}.svg`} alt="" width={40} height={40} />
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--landing-accent)', fontWeight: 600, textTransform: 'uppercase' }}>
                      {card.vertical}
                    </div>
                    <h3 style={{ fontSize: 16, margin: '4px 0 0' }}>{card.title}</h3>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                  <FeatureTag status="live" showDot={false} />
                  <span className="badge">{card.platform}</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--landing-text-muted)', marginBottom: 8 }}>{card.one_liner}</p>
                <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>{card.metric}</p>
                {card.persona.snippets[0] && (
                  <p style={{ fontSize: 12, color: 'var(--landing-text-muted)', fontStyle: 'italic', borderLeft: '2px solid var(--landing-accent)', paddingLeft: 10 }}>
                    {card.persona.snippets[0].text.slice(0, 140)}
                    {card.persona.snippets[0].text.length > 140 ? '...' : ''}
                  </p>
                )}
              </article>
            ))}
          </div>
        )}
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Link to="/showcase" className="landing-btn landing-btn-secondary">
            {t('landing.showcaseAllCta')}
          </Link>
        </div>
      </section>

      {/* --- How it works: 3 steps --- */}
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

      {/* --- Marketplace preview --- */}
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

      {/* --- Trust --- */}
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

      {/* --- Footer CTA --- */}
      <section className="landing-footer-cta">
        <h2>{t('landing.footerCtaTitle')}</h2>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="#live-demo" className="landing-btn landing-btn-primary">{t('landing.footerCtaDemo')}</a>
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
            <a href="#live-demo">{t('landing.navDemo')}</a>
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
