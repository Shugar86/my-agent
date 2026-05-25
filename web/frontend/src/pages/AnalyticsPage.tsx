import { useEffect, useMemo, useState } from 'react';
import { getUsageSummary, type UsageSummary } from '../api/appClient';

function compactNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
}

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

  const stats = useMemo(() => {
    if (!summary) return [];
    const avgCost = summary.workflow_runs > 0 ? summary.total_cost_usd / summary.workflow_runs : 0;
    return [
      { label: 'Tokens', value: compactNumber(summary.total_tokens) },
      { label: 'Cost (USD)', value: `$${summary.total_cost_usd.toFixed(4)}` },
      { label: 'Workflow runs', value: summary.workflow_runs },
      { label: 'Avg cost / run', value: `$${avgCost.toFixed(4)}` },
    ];
  }, [summary]);

  if (loading) {
    return (
      <div style={{ padding: 30 }}>
        <div className="skeleton" style={{ height: 40, width: 200, marginBottom: 24 }} />
        <div className="skeleton" style={{ height: 120 }} />
      </div>
    );
  }

  const daily = summary?.daily || [];
  const maxTokens = Math.max(...daily.map((d) => d.tokens), 1);
  const maxEvents = Math.max(...daily.map((d) => d.events), 1);

  return (
    <div style={{ padding: 30 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1>Analytics</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Workspace usage, runs, and costs</p>
        </div>
        <select className="input" style={{ width: 120 }} value={period} onChange={(e) => setPeriod(e.target.value as '7d' | '30d')}>
          <option value="7d">7 days</option>
          <option value="30d">30 days</option>
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 32 }}>
        {stats.map((s) => (
          <div key={s.label} className="card">
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.label}</div>
            <div style={{ fontSize: 26, color: 'var(--accent)', fontWeight: 600 }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 16, marginBottom: 24 }}>
        <section className="card">
          <h2 style={{ fontSize: 14, marginBottom: 16 }}>Tokens per day</h2>
          <DailyBarChart data={daily.map((d) => ({ label: d.day, value: d.tokens }))} max={maxTokens} accent="var(--accent)" />
        </section>
        <section className="card">
          <h2 style={{ fontSize: 14, marginBottom: 16 }}>Events per day</h2>
          <DailyBarChart data={daily.map((d) => ({ label: d.day, value: d.events }))} max={maxEvents} accent="var(--success)" />
        </section>
      </div>

      {summary?.top_workflows?.length ? (
        <section className="card">
          <h2 style={{ fontSize: 14, marginBottom: 12 }}>Top workflows</h2>
          {summary.top_workflows.map((w) => {
            const ratio = (w.runs / Math.max(1, summary.top_workflows[0].runs)) * 100;
            return (
              <div key={w.workflow_id} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                  <span style={{ fontFamily: 'monospace' }}>{w.workflow_id}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{w.runs} runs</span>
                </div>
                <div style={{ height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: `${ratio}%`, height: '100%', background: 'var(--accent)', transition: 'width 0.3s' }} />
                </div>
              </div>
            );
          })}
        </section>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: 32 }}>
          <p style={{ color: 'var(--text-muted)' }}>No workflow runs in this period yet.</p>
        </div>
      )}
    </div>
  );
}

interface BarPoint {
  label: string;
  value: number;
}

function DailyBarChart({ data, max, accent }: { data: BarPoint[]; max: number; accent: string }) {
  if (data.length === 0) {
    return <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No data yet</p>;
  }
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, minHeight: 140 }}>
      {data.map((d) => (
        <div key={d.label} style={{ flex: 1, textAlign: 'center', position: 'relative' }}>
          <div
            style={{
              height: `${Math.max(4, (d.value / max) * 120)}px`,
              background: `linear-gradient(180deg, ${accent} 0%, rgba(88,166,255,0.4) 100%)`,
              borderRadius: 4,
              marginBottom: 4,
              transition: 'height 0.4s ease',
            }}
            title={`${d.value.toLocaleString()} on ${d.label}`}
          />
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{String(d.label).slice(5)}</div>
        </div>
      ))}
    </div>
  );
}
