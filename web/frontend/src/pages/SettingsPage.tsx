import { useEffect, useState } from 'react';

export default function SettingsPage() {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <div style={{ padding: 30, maxWidth: 600 }}>
      <h1 style={{ marginBottom: 8 }}>Settings</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>Application configuration</p>

      <div className="card" style={{ marginBottom: 16 }}>
        <h2 style={{ fontSize: 15, marginBottom: 12 }}>System Status</h2>
        {health ? (
          <pre style={{ fontSize: 12, color: 'var(--text-muted)', overflow: 'auto' }}>
            {JSON.stringify(health, null, 2)}
          </pre>
        ) : (
          <div className="skeleton" style={{ height: 60 }} />
        )}
      </div>

      <div className="card">
        <h2 style={{ fontSize: 15, marginBottom: 12 }}>Integrations</h2>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>
          Connect Gmail, Google Sheets, Notion, and Telegram via onboarding.
        </p>
        <a href="/onboarding" className="btn btn-primary">Open Onboarding</a>
      </div>
    </div>
  );
}
