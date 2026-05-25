import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import './theme.css';

const NAV = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/chat', label: 'Chat', icon: '💬' },
  { to: '/workflows', label: 'Workflows', icon: '⚡' },
  { to: '/marketplace', label: 'Marketplace', icon: '🛒' },
  { to: '/builder', label: 'Agent Builder', icon: '🏗️' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
];

export default function AppShell() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <button
        className="mobile-toggle"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle menu"
        style={{
          display: 'none',
          position: 'fixed', top: 12, left: 12, zIndex: 1001,
          background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
          color: 'var(--text)', padding: '8px 12px', borderRadius: 6, cursor: 'pointer',
        }}
      >
        ☰
      </button>

      <aside
        className={`sidebar ${sidebarOpen ? 'open' : ''}`}
        style={{
          width: 'var(--sidebar-width)',
          minWidth: 'var(--sidebar-width)',
          background: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border)',
          padding: '20px 0',
          position: 'fixed',
          top: 0, bottom: 0, left: 0,
          zIndex: 1000,
          transition: 'transform 0.2s',
        }}
      >
        <h1 style={{ padding: '0 20px 20px', fontSize: '1.1rem', color: 'var(--accent)', borderBottom: '1px solid var(--border)', marginBottom: 10 }}>
          🤖 My Agent
        </h1>
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            onClick={() => setSidebarOpen(false)}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '12px 20px', color: isActive ? 'var(--text)' : 'var(--text-muted)',
              background: isActive ? 'var(--bg-tertiary)' : 'transparent',
              textDecoration: 'none', transition: 'all 0.15s',
            })}
          >
            <span>{item.icon}</span> {item.label}
          </NavLink>
        ))}
      </aside>

      <main style={{ marginLeft: 'var(--sidebar-width)', flex: 1, minHeight: '100vh' }}>
        <Outlet />
      </main>

      <style>{`
        @media (max-width: 768px) {
          .mobile-toggle { display: block !important; }
          .sidebar { transform: translateX(-100%); width: 240px !important; min-width: 240px !important; }
          .sidebar.open { transform: translateX(0); }
          main { margin-left: 0 !important; padding-top: 48px; }
        }
      `}</style>
    </div>
  );
}
