interface LogEntry {
  node_id: string;
  event: string;
  detail?: unknown;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60_000);
  const seconds = Math.round((ms % 60_000) / 1000);
  return `${minutes}m ${seconds}s`;
}

function extractDuration(detail: unknown): number | null {
  if (!detail || typeof detail !== 'object') return null;
  const d = detail as Record<string, unknown>;
  if (typeof d.duration_ms === 'number') return d.duration_ms;
  return null;
}

interface Props {
  logs: LogEntry[];
  activeNodeId?: string;
}

const EVENT_COLOR: Record<string, string> = {
  started: 'var(--accent)',
  completed: 'var(--success)',
  error: 'var(--danger)',
  skipped: 'var(--text-muted)',
  retry: 'var(--warning)',
  retry_success: 'var(--success)',
};

const EVENT_LABEL: Record<string, string> = {
  started: 'Started',
  completed: 'Completed',
  error: 'Failed',
  skipped: 'Skipped',
  retry: 'Retrying',
  retry_success: 'Recovered',
};

export default function ExecutionTimeline({ logs, activeNodeId }: Props) {
  if (!logs.length) {
    return <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>No execution logs yet.</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {logs.map((log, i) => {
        const color = EVENT_COLOR[log.event] || 'var(--border)';
        const isActive = log.node_id === activeNodeId && log.event === 'started';
        return (
          <div key={i} style={{ display: 'flex', gap: 12, position: 'relative' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 20 }}>
              <div
                style={{
                  width: 12, height: 12, borderRadius: '50%',
                  background: color,
                  border: isActive ? '2px solid var(--accent)' : 'none',
                  boxShadow: isActive ? '0 0 0 4px rgba(88,166,255,0.2)' : 'none',
                  animation: isActive ? 'pulseRing 1.4s infinite' : undefined,
                }}
              />
              {i < logs.length - 1 && (
                <div style={{ width: 2, flex: 1, background: 'var(--border)', minHeight: 24 }} />
              )}
            </div>
            <div style={{ paddingBottom: 14, flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 6 }}>
                <span style={{ fontSize: 12, fontWeight: 600 }}>{log.node_id}</span>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  {(() => {
                    const dur = extractDuration(log.detail);
                    return dur !== null ? (
                      <span style={{ fontSize: 10, color: 'var(--text-subtle)', fontVariantNumeric: 'tabular-nums' }}>
                        {formatDuration(dur)}
                      </span>
                    ) : null;
                  })()}
                  <span
                    style={{
                      fontSize: 10,
                      color,
                      border: `1px solid ${color}`,
                      padding: '1px 6px',
                      borderRadius: 8,
                    }}
                  >
                    {EVENT_LABEL[log.event] || log.event}
                  </span>
                </div>
              </div>
              {log.detail != null && (
                <pre
                  style={{
                    fontSize: 10,
                    color: 'var(--text-muted)',
                    marginTop: 4,
                    overflow: 'auto',
                    maxHeight: 60,
                    background: 'var(--bg)',
                    padding: 6,
                    borderRadius: 4,
                    border: '1px solid var(--border)',
                  }}
                >
                  {typeof log.detail === 'string' ? log.detail : JSON.stringify(log.detail, null, 2)}
                </pre>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
