interface LogEntry {
  node_id: string;
  event: string;
  detail?: unknown;
}

interface Props {
  logs: LogEntry[];
  activeNodeId?: string;
}

export default function ExecutionTimeline({ logs, activeNodeId }: Props) {
  if (!logs.length) {
    return <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>No execution logs yet</p>;
  }

  const eventColor: Record<string, string> = {
    started: 'var(--accent)',
    completed: 'var(--success)',
    error: '#f85149',
    skipped: 'var(--text-muted)',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {logs.map((log, i) => (
        <div key={i} style={{ display: 'flex', gap: 12, position: 'relative' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 20 }}>
            <div
              style={{
                width: 10, height: 10, borderRadius: '50%',
                background: log.node_id === activeNodeId ? 'var(--accent)' : (eventColor[log.event] || 'var(--border)'),
                border: log.node_id === activeNodeId ? '2px solid var(--accent)' : 'none',
              }}
            />
            {i < logs.length - 1 && (
              <div style={{ width: 2, flex: 1, background: 'var(--border)', minHeight: 24 }} />
            )}
          </div>
          <div style={{ paddingBottom: 16, flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600 }}>{log.node_id}</div>
            <div style={{ fontSize: 11, color: eventColor[log.event] || 'var(--text-muted)' }}>{log.event}</div>
            {log.detail != null && (
              <pre style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, overflow: 'auto', maxHeight: 60 }}>
                {typeof log.detail === 'string' ? log.detail : JSON.stringify(log.detail, null, 2)}
              </pre>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
