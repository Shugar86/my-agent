import { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import TeamSwitcher from '../components/TeamSwitcher';
import { getMe, type MeUser } from '../api/appClient';
import './theme.css';

const NAV = [
  { to: '/', label: 'Dashboard' },
  { to: '/chat', label: 'Chat' },
  { to: '/workflows', label: 'Workflows' },
  { to: '/marketplace', label: 'Marketplace' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/builder', label: 'Agent Builder' },
  { to: '/settings', label: 'Settings' },
];

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
        aria-label="Toggle menu"
        style={{
          display: 'none',
          position: 'fixed', top: 12, left: 12, zIndex: 1001,
        }}
      >
        Menu
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
          <h1 style={{ fontSize: '1.05rem', color: 'var(--accent)', letterSpacing: '-0.01em' }}>My Agent</h1>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Visual workflows for AI</p>
        </div>
        <TeamSwitcher />
        <nav style={{ flex: 1 }}>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={() => setSidebarOpen(false)}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 18px',
                color: isActive ? 'var(--text)' : 'var(--text-muted)',
                background: isActive ? 'var(--bg-tertiary)' : 'transparent',
                borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                textDecoration: 'none',
                fontSize: 13,
                fontWeight: isActive ? 500 : 400,
                transition: 'all 0.15s',
              })}
            >
              {item.label}
            </NavLink>
          ))}
          {showAdmin && (
            <NavLink
              to="/admin"
              onClick={() => setSidebarOpen(false)}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 18px',
                color: isActive ? 'var(--text)' : 'var(--text-muted)',
                background: isActive ? 'var(--bg-tertiary)' : 'transparent',
                borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
                textDecoration: 'none',
                fontSize: 13,
              })}
            >
              Admin
            </NavLink>
          )}
        </nav>
        <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Theme</span>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            style={{ padding: '4px 8px', fontSize: 11 }}
          >
            {theme === 'dark' ? 'Light' : 'Dark'}
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
          main { margin-left: 0 !important; padding-top: 56px; }
        }
      `}</style>
    </div>
  );
}
