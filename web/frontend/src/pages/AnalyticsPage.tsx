import { useEffect, useState } from 'react';
import { getUsageSummary, type UsageSummary } from '../api/appClient';

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'7d' | '30d'>('7d');
  const [summary, setSummary] = useState<UsageSummary | null>(null);

  useEffect(() => {
    setLoading(true);
    getUsageSummary(period)
      .then(setSummary)
      .catch(() => setSummary(null))
      .finally(() => setLoading(false));
  }, [period]);

  if (loading) {
    return (
      <div style={{ padding: 30 }}>
        <div className="skeleton" style={{ height: 40, width: 200, marginBottom: 24 }} />
        <div className="skeleton" style={{ height: 120 }} />
      </div>
    );
  }

  const maxTokens = Math.max(...(summary?.daily.map((d) => d.tokens) || [1]), 1);

  return (
    <div style={{ padding: 30 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1>Analytics</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Workspace usage and costs</p>
        </div>
        <select className="input" style={{ width: 120 }} value={period} onChange={(e) => setPeriod(e.target.value as '7d' | '30d')}>
          <option value="7d">7 days</option>
          <option value="30d">30 days</option>
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 32 }}>
        {[
          { label: 'Tokens', value: summary?.total_tokens ?? 0 },
          { label: 'Cost (USD)', value: `$${(summary?.total_cost_usd ?? 0).toFixed(4)}` },
          { label: 'Workflow runs', value: summary?.workflow_runs ?? 0 },
          { label: 'Events', value: summary?.event_count ?? 0 },
        ].map((s) => (
          <div key={s.label} className="card">
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.label}</div>
            <div style={{ fontSize: 24, color: 'var(--accent)', fontWeight: 600 }}>{s.value}</div>
          </div>
        ))}
      </div>

      <section className="card" style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 14, marginBottom: 16 }}>Tokens per day</h2>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, minHeight: 120 }}>
          {(summary?.daily || []).map((d) => (
            <div key={d.day} style={{ flex: 1, textAlign: 'center' }}>
              <div
                style={{
                  height: `${Math.max(4, (d.tokens / maxTokens) * 100)}px`,
                  background: 'var(--accent)',
                  borderRadius: 4,
                  marginBottom: 4,
                }}
                title={`${d.tokens} tokens`}
              />
              <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{String(d.day).slice(-5)}</div>
            </div>
          ))}
          {!summary?.daily?.length && (
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No usage data yet</p>
          )}
        </div>
      </section>

      {summary?.top_workflows?.length ? (
        <section className="card">
          <h2 style={{ fontSize: 14, marginBottom: 12 }}>Top workflows</h2>
          {summary.top_workflows.map((w) => (
            <div key={w.workflow_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
              <span style={{ fontSize: 13 }}>{w.workflow_id}</span>
              <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{w.runs} runs</span>
            </div>
          ))}
        </section>
      ) : null}
    </div>
  );
}
