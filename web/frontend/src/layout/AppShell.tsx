import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import TeamSwitcher from '../components/TeamSwitcher';
import { getMe, type MeUser } from '../api/appClient';
import { t } from '../i18n';
import './theme.css';

const NAV_MAIN = [
  { to: '/', labelKey: 'nav.dashboard' as const },
  { to: '/showcase', labelKey: 'nav.showcase' as const },
  { to: '/chat', labelKey: 'nav.chat' as const },
  { to: '/workflows', labelKey: 'nav.workflows' as const },
  { to: '/marketplace', labelKey: 'nav.marketplace' as const },
  { to: '/analytics', labelKey: 'nav.analytics' as const },
];

const NAV_POWER = [
  { to: '/agents', labelKey: 'nav.agents' as const },
  { to: '/knowledge', labelKey: 'nav.knowledge' as const },
  { to: '/mcp', labelKey: 'nav.mcp' as const },
  { to: '/settings', labelKey: 'nav.settings' as const },
];

function navLinkStyle(isActive: boolean) {
  return {
    display: 'flex' as const,
    alignItems: 'center' as const,
    gap: 10,
    padding: '10px 18px',
    color: isActive ? 'var(--text)' : 'var(--text-muted)',
    background: isActive ? 'var(--bg-tertiary)' : 'transparent',
    borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
    textDecoration: 'none' as const,
    fontSize: 13,
    fontWeight: isActive ? 500 : 400,
    transition: 'all 0.15s',
  };
}

const THEME_STORAGE_KEY = 'my-agent.theme';

function applyTheme(theme: 'dark' | 'light') {
  document.documentElement.dataset.theme = theme;
}

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [me, setMe] = useState<MeUser | null>(null);
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem(THEME_STORAGE_KEY) : null;
    return stored === 'light' ? 'light' : 'dark';
  });

  useEffect(() => {
    applyTheme(theme);
    if (typeof window !== 'undefined') localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    getMe().then(setMe).catch(() => {});
  }, []);

  const showAdmin = me?.role === 'admin' || me?.team_role === 'owner' || me?.team_role === 'admin';

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <button
        className="mobile-toggle btn"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label={t('app.menu')}
        style={{
          display: 'none',
          position: 'fixed', top: 12, left: 12, zIndex: 1001,
        }}
      >
        {t('app.menu')}
      </button>

      <aside
        className={`sidebar ${sidebarOpen ? 'open' : ''}`}
        style={{
          width: 'var(--sidebar-width)',
          minWidth: 'var(--sidebar-width)',
          background: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border)',
          padding: '16px 0',
          position: 'fixed',
          top: 0, bottom: 0, left: 0,
          zIndex: 1000,
          transition: 'transform 0.2s',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div style={{ padding: '0 18px 14px', borderBottom: '1px solid var(--border)', marginBottom: 8 }}>
          <h1 style={{ fontSize: '1.05rem', color: 'var(--accent)', letterSpacing: '-0.01em' }}>{t('app.title')}</h1>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{t('app.tagline')}</p>
        </div>
        <TeamSwitcher />
        <nav style={{ flex: 1, overflowY: 'auto' }}>
          {NAV_MAIN.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={() => setSidebarOpen(false)}
              style={({ isActive }) => navLinkStyle(isActive)}
            >
              {t(item.labelKey)}
            </NavLink>
          ))}
          <div style={{ margin: '8px 18px', borderTop: '1px solid var(--border)' }} />
          {NAV_POWER.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              style={({ isActive }) => navLinkStyle(isActive)}
            >
              {t(item.labelKey)}
            </NavLink>
          ))}
          {showAdmin && (
            <NavLink
              to="/admin"
              onClick={() => setSidebarOpen(false)}
              style={({ isActive }) => navLinkStyle(isActive)}
            >
              {t('nav.admin')}
            </NavLink>
          )}
        </nav>
        <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{t('app.theme')}</span>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            style={{ padding: '4px 8px', fontSize: 11 }}
          >
            {theme === 'dark' ? t('app.themeLight') : t('app.themeDark')}
          </button>
        </div>
      </aside>

      <main style={{ marginLeft: 'var(--sidebar-width)', flex: 1, minHeight: '100vh' }}>
        <Outlet />
      </main>

      <style>{`
        @media (max-width: 768px) {
          .mobile-toggle { display: inline-flex !important; }
          .sidebar { transform: translateX(-100%); width: 240px !important; min-width: 240px !important; }
          .sidebar.open { transform: translateX(0); }
          main { margin-left: 0 !important; }
        }
      `}</style>
    </div>
  );
}
