import { useEffect, useState } from 'react';
import {
  listMcpServers,
  startMcpServer,
  stopMcpServer,
  startAllMcp,
  stopAllMcp,
  type McpServer,
} from '../api/appClient';
import PageHeader from '../components/ui/PageHeader';
import EmptyState from '../components/ui/EmptyState';
import { useToast } from '../components/ui/Toast';
import { t } from '../i18n';

/** MCP server management — migrated from legacy mcp.html. */
export default function McpPage() {
  const { showToast } = useToast();
  const [servers, setServers] = useState<McpServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    listMcpServers()
      .then(setServers)
      .catch(() => setServers([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleStart = async (name: string) => {
    setBusy(name);
    try {
      const data = await startMcpServer(name);
      showToast(
        data.success
          ? t('mcp.started', { name, tools: String(data.tools ?? 0) })
          : (data.error || t('common.error')),
        data.success ? 'success' : 'error',
      );
      load();
    } catch {
      showToast(t('common.error'), 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleStop = async (name: string) => {
    setBusy(name);
    try {
      const data = await stopMcpServer(name);
      showToast(data.success ? t('mcp.stopped', { name }) : (data.error || t('common.error')), data.success ? 'success' : 'error');
      load();
    } catch {
      showToast(t('common.error'), 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleStartAll = async () => {
    setBusy('all');
    try {
      await startAllMcp();
      load();
      showToast(t('common.success'));
    } catch {
      showToast(t('common.error'), 'error');
    } finally {
      setBusy(null);
    }
  };

  const handleStopAll = async () => {
    setBusy('all');
    try {
      await stopAllMcp();
      load();
      showToast(t('common.success'));
    } catch {
      showToast(t('common.error'), 'error');
    } finally {
      setBusy(null);
    }
  };

  const statusLabel = (s: McpServer) => {
    if (s.connected) return t('mcp.connected');
    if (s.enabled) return t('mcp.pending');
    return t('mcp.disconnected');
  };

  return (
    <div className="page-content">
      <PageHeader
        title={t('mcp.title')}
        subtitle={t('mcp.subtitle')}
        actions={
          <>
            <button type="button" className="btn" onClick={handleStartAll} disabled={busy === 'all'}>{t('common.startAll')}</button>
            <button type="button" className="btn" onClick={handleStopAll} disabled={busy === 'all'}>{t('common.stopAll')}</button>
            <button type="button" className="btn" onClick={load} aria-label={t('common.refresh')}>🔄</button>
          </>
        }
      />

      {loading ? (
        <div className="cards-grid">
          {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 160 }} />)}
        </div>
      ) : servers.length === 0 ? (
        <EmptyState title={t('mcp.empty')} />
      ) : (
        <div className="cards-grid">
          {servers.map((s) => (
            <div key={s.name} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <strong>{s.name}</strong>
                <span className={`badge ${s.connected ? 'badge-success' : ''}`}>{statusLabel(s)}</span>
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                <div>{t('mcp.toolsCount')}: <strong>{s.tools_count}</strong></div>
                <div>{t('mcp.command')}: <code>{s.command || '—'}</code></div>
                <div>{t('mcp.status')}: {s.enabled ? t('mcp.enabled') : t('mcp.disabled')}</div>
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={s.connected || busy === s.name}
                  onClick={() => handleStart(s.name)}
                >
                  {t('common.start')}
                </button>
                <button
                  type="button"
                  className="btn btn-danger"
                  disabled={!s.connected || busy === s.name}
                  onClick={() => handleStop(s.name)}
                >
                  {t('common.stop')}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
