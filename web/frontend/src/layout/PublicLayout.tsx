import { Link, Outlet } from 'react-router-dom';
import ProductNarrative from '../components/ProductNarrative';
import { loginUrl } from '../lib/routes';
import { t } from '../i18n';
import './landing.css';

function BrandLogo() {
  return (
    <svg className="brand-logo" viewBox="0 0 40 40" fill="none" width={32} height={32} aria-hidden>
      <circle cx="20" cy="20" r="18" stroke="currentColor" strokeWidth="3" />
      <circle cx="20" cy="20" r="7" fill="currentColor" />
    </svg>
  );
}

/** Marketing shell for public routes (/, /demo, /showcase). */
export default function PublicLayout() {
  return (
    <div className="landing-root">
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <Link to="/" className="landing-brand">
            <BrandLogo />
            <span>{t('app.title')}</span>
          </Link>
          <div className="landing-nav-links">
            <Link to="/showcase">{t('nav.showcase')}</Link>
            <a href="/#product">{t('landing.navProduct')}</a>
            <a href="/#pricing">{t('landing.navPricing')}</a>
            <Link to="/demo">{t('landing.navDemo')}</Link>
          </div>
          <a href={loginUrl()} className="landing-btn landing-btn-primary">
            {t('landing.navLogin')}
          </a>
        </div>
      </nav>
      <ProductNarrative variant="strip" context="landing" />
      <Outlet />
    </div>
  );
}
