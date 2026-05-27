import { useEffect, useState } from 'react';
import PlaygroundDemo from '../components/demo/PlaygroundDemo';
import FeatureTag from '../components/ui/FeatureTag';
import { SHOWCASE_CARD_TEMPLATES, showcaseCardFeatureStatus } from '../config/showcaseCards';
import { getPageFeatureStatus } from '../config/featureRegistry';
import { COMPETITOR_DEMO_PRESETS } from '../lib/demoNodeLabels';
import { useDemoAwareFetch } from '../hooks/useDemoAwareFetch';
import { loginUrl } from '../lib/routes';
import { t } from '../i18n';

interface PersonaSnippet {
  type?: string;
  text: string;
}

interface ShowcaseCard {
  id: string;
  vertical: string;
  title: string;
  one_liner: string;
  status: 'live' | 'lab';
  platform: string;
  metric: string;
  icon: string;
  cta_label: string;
  cta_url: string | null;
  persona: {
    role: string;
    voice: string;
    snippets: PersonaSnippet[];
  };
}

interface ShowcaseData {
  meta: { live_deployments: number; personas: number; templates: number };
  cards: ShowcaseCard[];
}

/** Public showcase at `/showcase` — vertical cases + playground, install redirects to login. */
export default function PublicShowcasePage() {
  const { data, source, loading } = useDemoAwareFetch<ShowcaseData>('/welcome-assets/data/showcase.json');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showStickyCta, setShowStickyCta] = useState(false);

  useEffect(() => {
    const onScroll = () => {
      const playground = document.getElementById('playground');
      if (!playground) return;
      const rect = playground.getBoundingClientRect();
      setShowStickyCta(rect.top > window.innerHeight || rect.bottom < 120);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, [loading, data]);

  if (loading || !data) {
    return (
      <div className="landing-section">
        <div className="skeleton" style={{ height: 48, marginBottom: 24 }} />
        <div className="landing-cards-grid">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton" style={{ height: 220 }} />
          ))}
        </div>
      </div>
    );
  }

  const meta = data.meta;

  return (
    <div className="landing-section">
      {showStickyCta && (
        <a
          href="#playground"
          className="landing-btn landing-btn-primary"
          style={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 100,
            boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
          }}
        >
          {t('showcase.canonicalCta')}
        </a>
      )}

      <div className="landing-section-header">
        <span className="landing-section-tag">{t('nav.showcase')}</span>
        <FeatureTag status={getPageFeatureStatus('showcase.playground')} showDot={false} />
        <h1 className="landing-section-title">{t('showcase.title')}</h1>
        <p className="landing-section-desc">{t('showcase.canonicalDesc')}</p>
        <p className="landing-section-desc" style={{ marginTop: 8 }}>
          {t('showcase.subtitle', {
            live: meta.live_deployments,
            personas: meta.personas,
            templates: meta.templates,
          })}
        </p>
        <a href="#playground" className="landing-btn landing-btn-primary" style={{ marginTop: 16 }}>
          {t('showcase.canonicalCta')}
        </a>
        {source === 'mock' && (
          <FeatureTag status="mock" label={t('featureTag.previewData')} showDot={false} />
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <h2 style={{ fontSize: '1rem', margin: 0 }}>{t('showcase.verticalCasesTitle')}</h2>
        <FeatureTag status={getPageFeatureStatus('showcase.cards')} showDot={false} />
      </div>

      <div className="landing-cards-grid" style={{ marginBottom: 48 }}>
        {data.cards.map((card) => (
          <article
            key={card.id}
            className="landing-card"
            style={{ borderStyle: card.status === 'lab' ? 'dashed' : 'solid' }}
          >
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
              <FeatureTag
                status={showcaseCardFeatureStatus(card)}
                label={card.status === 'lab' ? t('showcase.labBadge') : undefined}
                showDot={false}
              />
              <span className="badge">{card.platform}</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--landing-text-muted)', marginBottom: 8 }}>{card.one_liner}</p>
            <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>{card.metric}</p>
            <button
              type="button"
              className="landing-btn landing-btn-secondary"
              style={{ fontSize: 12, padding: '4px 12px', marginBottom: 12 }}
              onClick={() => setExpanded(expanded === card.id ? null : card.id)}
            >
              {expanded === card.id ? t('showcase.personaHide') : t('showcase.personaToggle')}
            </button>
            {expanded === card.id && (
              <div style={{ fontSize: 12, background: 'var(--landing-bg-secondary)', borderRadius: 8, padding: 12, marginBottom: 12 }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{card.persona.role}</div>
                <div style={{ color: 'var(--landing-text-muted)', fontStyle: 'italic', marginBottom: 8 }}>{card.persona.voice}</div>
                {card.persona.snippets.map((s, i) => (
                  <div key={i} style={{ marginBottom: 6, paddingLeft: 8, borderLeft: '2px solid var(--landing-accent)' }}>
                    {s.text}
                  </div>
                ))}
              </div>
            )}
            {card.cta_url ? (
              <a href={card.cta_url} className="landing-btn landing-btn-secondary" target="_blank" rel="noopener noreferrer" style={{ width: '100%' }}>
                {card.cta_label} ↗
              </a>
            ) : card.id === 'my-agent' ? (
              <a href="#playground" className="landing-btn landing-btn-primary" style={{ width: '100%' }}>
                {card.cta_label}
              </a>
            ) : SHOWCASE_CARD_TEMPLATES[card.id] ? (
              <a href={loginUrl('/app/onboarding')} className="landing-btn landing-btn-primary" style={{ width: '100%' }}>
                {t('showcase.installSimilar')}
              </a>
            ) : (
              <a href="#playground" className="landing-btn landing-btn-secondary" style={{ width: '100%' }}>
                {t('landing.heroPrimaryCta')}
              </a>
            )}
          </article>
        ))}
      </div>

      <div id="playground" style={{ marginBottom: 48 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <h2 className="landing-section-title" style={{ fontSize: '1.25rem', margin: 0 }}>{t('playground.title')}</h2>
          <FeatureTag status={getPageFeatureStatus('showcase.playground')} showDot={false} />
        </div>
        <div className="landing-demo-embed">
          <PlaygroundDemo
            publicMode
            lockPreset="competitor"
            presets={COMPETITOR_DEMO_PRESETS}
          />
        </div>
      </div>

      <div id="cta" className="landing-footer-cta" style={{ borderRadius: 12, marginTop: 24 }}>
        <h2>{t('landing.showcaseLeadTitle')}</h2>
        <p style={{ color: 'var(--landing-text-muted)', marginBottom: 20 }}>{t('landing.showcaseLeadDesc')}</p>
        <a href={loginUrl('/app/onboarding')} className="landing-btn landing-btn-primary">
          {t('landing.showcaseLeadCta')}
        </a>
      </div>
    </div>
  );
}
