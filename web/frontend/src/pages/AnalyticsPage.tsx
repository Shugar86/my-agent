import { useEffect, useMemo, useState } from 'react';
import { getUsageSummary, type UsageSummary } from '../api/appClient';
import { listWorkflows } from '../api/workflowClient';
import { t } from '../i18n';

function compactNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
}

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'7d' | '30d'>('7d');
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [workflowNames, setWorkflowNames] = useState<Record<string, string>>({});

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getUsageSummary(period).catch(() => null),
      listWorkflows().catch(() => []),
    ])
      .then(([usage, workflows]) => {
        setSummary(usage);
        const names: Record<string, string> = {};
        workflows.forEach((w) => { names[w.id] = w.name; });
        setWorkflowNames(names);
      })
      .finally(() => setLoading(false));
  }, [period]);

  const stats = useMemo(() => {
    if (!summary) return [];
    const avgCost = summary.workflow_runs > 0 ? summary.total_cost_usd / summary.workflow_runs : 0;
    return [
      { label: t('analytics.tokens'), value: compactNumber(summary.total_tokens) },
      { label: t('analytics.cost'), value: `$${summary.total_cost_usd.toFixed(4)}` },
      { label: t('analytics.runs'), value: summary.workflow_runs },
      { label: t('analytics.avgCost'), value: `$${avgCost.toFixed(4)}` },
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
  const hasRuns = (summary?.workflow_runs ?? 0) > 0;

  return (
    <div style={{ padding: 30 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1>{t('analytics.title')}</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t('analytics.subtitle')}</p>
        </div>
        <select className="input" style={{ width: 120 }} value={period} onChange={(e) => setPeriod(e.target.value as '7d' | '30d')}>
          <option value="7d">{t('analytics.period7')}</option>
          <option value="30d">{t('analytics.period30')}</option>
        </select>
      </div>

      {hasRuns && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 32 }}>
          {stats.map((s) => (
            <div key={s.label} className="card">
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.label}</div>
              <div style={{ fontSize: 26, color: 'var(--accent)', fontWeight: 600 }}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {hasRuns && daily.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 16, marginBottom: 24 }}>
          <section className="card">
            <h2 style={{ fontSize: 14, marginBottom: 16 }}>{t('analytics.tokensPerDay')}</h2>
            <DailyBarChart data={daily.map((d) => ({ label: d.day, value: d.tokens }))} max={maxTokens} accent="var(--accent)" />
          </section>
          <section className="card">
            <h2 style={{ fontSize: 14, marginBottom: 16 }}>{t('analytics.eventsPerDay')}</h2>
            <DailyBarChart data={daily.map((d) => ({ label: d.day, value: d.events }))} max={maxEvents} accent="var(--success)" />
          </section>
        </div>
      )}

      {summary?.top_workflows?.length ? (
        <section className="card">
          <h2 style={{ fontSize: 14, marginBottom: 12 }}>{t('analytics.topWorkflows')}</h2>
          {summary.top_workflows.map((w) => {
            const ratio = (w.runs / Math.max(1, summary.top_workflows[0].runs)) * 100;
            const displayName = workflowNames[w.workflow_id] || w.workflow_id;
            return (
              <div key={w.workflow_id} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                  <span>{displayName}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{t('analytics.runsCount', { count: w.runs })}</span>
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
          <p style={{ color: 'var(--text-muted)', marginBottom: 16 }}>{t('analytics.noRunsYet')}</p>
          <p style={{ fontSize: 13, marginBottom: 16 }}>{t('analytics.emptyCta')}</p>
          <a href="/demo" className="btn btn-primary">{t('analytics.emptyCtaLink')}</a>
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
    return <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>{t('analytics.noDataYet')}</p>;
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
