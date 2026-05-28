import { useState } from 'react';
import { getAgentPreview, agentPreviewChat, type AgentPreviewResult } from '../../api/appClient';
import FeatureTag from '../ui/FeatureTag';
import { loginUrl } from '../../lib/routes';
import { t } from '../../i18n';

const PLACEHOLDERS = [
  'AI-консультант для салона красоты: цены, запись, Telegram',
  'Менеджер поддержки для SaaS: FAQ, эскалация, Slack',
  'Контент-менеджер для Telegram-канала: 2 поста в день',
];

interface Props {
  compact?: boolean;
}

export default function AgentPreviewWidget({ compact = false }: Props) {
  const [task, setTask] = useState('');
  const [loading, setLoading] = useState(false);
  const [agent, setAgent] = useState<AgentPreviewResult | null>(null);
  const [error, setError] = useState('');
  const [chatMsg, setChatMsg] = useState('');
  const [chatReply, setChatReply] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [placeholder] = useState(() => PLACEHOLDERS[Math.floor(Math.random() * PLACEHOLDERS.length)]);

  const handleCreate = async () => {
    if (!task.trim() || task.trim().length < 5) return;
    setLoading(true);
    setError('');
    setAgent(null);
    setChatReply('');
    try {
      const result = await getAgentPreview(task.trim());
      setAgent(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('agentPreview.createError'));
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!chatMsg.trim() || !agent) return;
    setChatLoading(true);
    setChatReply('');
    try {
      const reply = await agentPreviewChat(agent.role, chatMsg.trim());
      setChatReply(reply);
    } catch {
      setChatReply(t('agentPreview.chatError'));
    } finally {
      setChatLoading(false);
    }
  };

  const handleReset = () => {
    setAgent(null);
    setChatReply('');
    setChatMsg('');
    setError('');
  };

  return (
    <section className={`playground-demo ${compact ? 'playground-demo--compact' : ''}`}>
      {!agent && !loading && (
        <>
          {!compact && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
              <h2 style={{ fontSize: 18, margin: 0 }}>{t('agentPreview.title')}</h2>
              <FeatureTag status="live" label="Live AI" showDot={false} />
            </div>
          )}
          <div style={{ display: 'grid', gap: 12, maxWidth: 520 }}>
            <div>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                {t('agentPreview.taskLabel')}
              </label>
              <textarea
                className="input"
                rows={3}
                value={task}
                onChange={(e) => setTask(e.target.value)}
                placeholder={placeholder}
                style={{ resize: 'vertical' }}
              />
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleCreate}
              disabled={loading || task.trim().length < 5}
            >
              {t('agentPreview.create')}
            </button>
          </div>
        </>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: 32 }}>
          <div className="skeleton" style={{ height: 160, marginBottom: 12 }} />
          <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{t('agentPreview.generating')}</p>
        </div>
      )}

      {error && (
        <div className="playground-error" role="alert">
          {error}
          <button type="button" className="btn btn-ghost" onClick={handleReset} style={{ marginLeft: 12 }}>
            {t('agentPreview.tryAgain')}
          </button>
        </div>
      )}

      {agent && (
        <div className="card" style={{ padding: 20, maxWidth: 560 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start', marginBottom: 16 }}>
            <span style={{ fontSize: 36 }}>{agent.icon}</span>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <h3 style={{ margin: 0, fontSize: 16 }}>{agent.name}</h3>
                <FeatureTag status="live" label="Live AI" showDot={false} />
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '6px 0 0' }}>{agent.role}</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
            {agent.skills.map((s) => (
              <span key={s} className="badge">{s}</span>
            ))}
          </div>

          {agent.sample_response && (
            <div style={{ background: 'var(--bg-secondary)', borderRadius: 12, padding: 14, marginBottom: 16, borderLeft: '3px solid var(--accent)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>{t('agentPreview.sampleLabel')}</div>
              <div style={{ fontSize: 14 }}>{agent.sample_response}</div>
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
              {t('agentPreview.chatLabel')}
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                className="input"
                value={chatMsg}
                onChange={(e) => setChatMsg(e.target.value)}
                placeholder={t('agentPreview.chatPlaceholder')}
                onKeyDown={(e) => { if (e.key === 'Enter') handleChat(); }}
                disabled={chatLoading}
                style={{ flex: 1 }}
              />
              <button type="button" className="btn btn-primary" onClick={handleChat} disabled={chatLoading || !chatMsg.trim()}>
                {chatLoading ? '…' : '→'}
              </button>
            </div>
          </div>

          {chatReply && (
            <div style={{ background: 'var(--bg-secondary)', borderRadius: 12, padding: 14, marginBottom: 16, borderLeft: '3px solid var(--accent)' }}>
              <div style={{ fontSize: 14 }}>{chatReply}</div>
            </div>
          )}

          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <a href={loginUrl('/app/settings?tab=agents')} className="btn btn-primary">
              {t('agentPreview.save')}
            </a>
            <button type="button" className="btn btn-ghost" onClick={handleReset}>
              {t('agentPreview.another')}
            </button>
          </div>
        </div>
      )}

      {!compact && !agent && !loading && (
        <p style={{ fontSize: 11, color: 'var(--text-subtle)', marginTop: 12 }}>
          {t('agentPreview.footer')}
        </p>
      )}
    </section>
  );
}
