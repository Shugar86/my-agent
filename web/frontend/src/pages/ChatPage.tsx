import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  listAgents,
  streamChat,
  listChatSessions,
  createChatSession,
  getChatMessages,
  listWorkflows,
  runWorkflowById,
  submitFeedback,
  logUxEvent,
  type Agent,
  type ChatSession,
} from '../api/appClient';
import ChatMarkdown from '../components/chat/ChatMarkdown';
import EmptyState from '../components/ui/EmptyState';
import { t } from '../i18n';

type MessageRole = 'user' | 'assistant' | 'tool-call' | 'tool-result';

interface Message {
  id: string;
  role: MessageRole;
  content: string;
  query?: string;
  feedback?: 1 | -1;
}

const EXAMPLE_PROMPTS = [
  'Проанализируй конкурентов в нише SaaS',
  'Составь план автоматизации поддержки',
  '/run competitor',
];

/** Multi-thread chat with markdown, tool bubbles, feedback, and workflow commands. */
export default function ChatPage() {
  const [searchParams] = useSearchParams();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentId, setAgentId] = useState(searchParams.get('agent') || 'universal');
  const [threads, setThreads] = useState<ChatSession[]>([]);
  const [activeThread, setActiveThread] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [threadsOpen, setThreadsOpen] = useState(false);
  const [lastUserQuery, setLastUserQuery] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const loadThreads = () => {
    listChatSessions()
      .then((sessions) => {
        setThreads(sessions);
        if (sessions.length > 0 && !activeThread) {
          setActiveThread(sessions[0].id);
        }
      })
      .catch(() => setThreads([]));
  };

  useEffect(() => {
    listAgents().then((list) => {
      setAgents(Array.isArray(list) ? list : []);
      if (!searchParams.get('agent') && list.length > 0) {
        setAgentId(list[0].id);
      }
    });
    loadThreads();
    logUxEvent('chat_page_view');
  }, [searchParams]);

  useEffect(() => {
    if (!activeThread) {
      setMessages([]);
      return;
    }
    getChatMessages(activeThread)
      .then((msgs) =>
        setMessages(
          msgs.map((m, i) => ({
            id: `${activeThread}-${i}`,
            role: m.role as MessageRole,
            content: m.content,
          })),
        ),
      )
      .catch(() => setMessages([]));
  }, [activeThread]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [input]);

  const handleRunCommand = async (text: string): Promise<string | null> => {
    const match = text.match(/^\/run\s+(.+)/i);
    if (!match) return null;
    const query = match[1].trim();
    const workflows = await listWorkflows();
    const wf = workflows.find((w) => w.id === query || w.name.toLowerCase() === query.toLowerCase())
      || workflows.find((w) => w.name.toLowerCase().includes(query.toLowerCase()));
    if (!wf) return `${t('chat.workflowNotFound')} ${query}`;
    try {
      const result = await runWorkflowById(wf.id, { chat_trigger: true }) as { success: boolean; run_id?: string; error?: string };
      return result.success
        ? t('chat.workflowDone', { name: wf.name, runId: result.run_id || '—' })
        : `${t('chat.workflowFailed')} ${result.error || 'unknown'}`;
    } catch {
      return `${t('chat.runFailed')} "${query}"`;
    }
  };

  const sendMessage = async (textOverride?: string) => {
    const userMsg = (textOverride ?? input).trim();
    if (!userMsg || streaming) return;
    setInput('');
    setStreaming(true);
    setLastUserQuery(userMsg);

    let threadId = activeThread;
    if (!threadId) {
      const created = await createChatSession(userMsg.slice(0, 40), agentId);
      threadId = created.id;
      setActiveThread(threadId);
      loadThreads();
    }

    const assistantId = `msg-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: 'user', content: userMsg },
      { id: assistantId, role: 'assistant', content: '', query: userMsg },
    ]);

    const runResult = await handleRunCommand(userMsg);
    if (runResult !== null) {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, content: runResult } : m)),
      );
      setStreaming(false);
      return;
    }

    let assistantText = '';
    try {
      await streamChat(userMsg, agentId, (event) => {
        if (event.type === 'token' && typeof event.content === 'string') {
          assistantText += event.content;
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: assistantText } : m)),
          );
        }
        if (event.type === 'tool_call') {
          const name = String(event.name || 'tool');
          const args = String(event.args || '');
          setMessages((prev) => [
            ...prev,
            {
              id: `tool-${Date.now()}-${name}`,
              role: 'tool-call',
              content: `${t('chat.toolCall')}: ${name}(${args})`,
            },
          ]);
        }
        if (event.type === 'tool_result') {
          const name = String(event.name || 'tool');
          const content = String(event.content || '').slice(0, 300);
          setMessages((prev) => [
            ...prev,
            {
              id: `result-${Date.now()}-${name}`,
              role: 'tool-result',
              content: `${t('chat.toolResult')} ${name}:\n${content}`,
            },
          ]);
        }
      }, threadId);
      logUxEvent('chat_message_sent', { agent_id: agentId });
      loadThreads();
    } catch {
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, content: t('chat.responseError') } : m)),
      );
    }
    setStreaming(false);
  };

  const handleFeedback = async (msg: Message, rating: 1 | -1) => {
    if (!activeThread || msg.feedback) return;
    try {
      await submitFeedback({
        session_id: activeThread,
        message_id: msg.id,
        query: msg.query || lastUserQuery,
        response: msg.content,
        rating,
        agent_id: agentId,
      });
      setMessages((prev) =>
        prev.map((m) => (m.id === msg.id ? { ...m, feedback: rating } : m)),
      );
    } catch { /* ignore */ }
  };

  const newThread = async () => {
    const created = await createChatSession('Новый чат', agentId);
    setThreads((prev) => [created, ...prev]);
    setActiveThread(created.id);
    setMessages([]);
    setThreadsOpen(false);
  };

  const renderBubble = (m: Message) => {
    const isUser = m.role === 'user';
    const isTool = m.role === 'tool-call' || m.role === 'tool-result';
    return (
      <div
        key={m.id}
        className={`chat-bubble ${isUser ? 'chat-bubble--user' : isTool ? `chat-bubble--${m.role}` : 'chat-bubble--assistant'}`}
      >
        {!isUser && !isTool && (
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>assistant</div>
        )}
        {m.role === 'assistant' && m.content ? (
          <ChatMarkdown content={m.content} />
        ) : (
          <div style={{ whiteSpace: 'pre-wrap', fontSize: 14 }}>
            {m.content || (streaming && m.role === 'assistant' ? '…' : '')}
          </div>
        )}
        {m.role === 'assistant' && m.content && !streaming && (
          <div className="feedback-bar">
            <button
              type="button"
              className={m.feedback === 1 ? 'voted-up' : ''}
              onClick={() => handleFeedback(m, 1)}
              aria-label="Полезно"
            >
              👍
            </button>
            <button
              type="button"
              className={m.feedback === -1 ? 'voted-down' : ''}
              onClick={() => handleFeedback(m, -1)}
              aria-label="Не полезно"
            >
              👎
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="chat-layout">
      {threadsOpen && (
        <button
          type="button"
          className="chat-threads-backdrop"
          aria-label="Закрыть список чатов"
          onClick={() => setThreadsOpen(false)}
        />
      )}
      <aside className={`chat-threads ${threadsOpen ? 'open' : ''}`}>
        <button type="button" className="btn btn-primary" style={{ width: '100%', marginBottom: 12 }} onClick={newThread}>
          {t('chat.newChat')}
        </button>
        {threads.map((th) => (
          <button
            key={th.id}
            type="button"
            className="btn"
            style={{
              width: '100%',
              marginBottom: 6,
              textAlign: 'left',
              background: th.id === activeThread ? 'var(--bg-tertiary)' : undefined,
            }}
            onClick={() => { setActiveThread(th.id); setThreadsOpen(false); }}
          >
            {th.title || t('chat.newChat')}
          </button>
        ))}
      </aside>

      <div className="chat-main">
        <div className="chat-toolbar">
          <button type="button" className="btn mobile-toggle" style={{ display: 'none' }} onClick={() => setThreadsOpen(true)}>
            ☰
          </button>
          <select className="input" style={{ width: 'auto', minWidth: 160 }} value={agentId} onChange={(e) => setAgentId(e.target.value)}>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>{a.name || a.id}</option>
            ))}
            {agents.length === 0 && <option value="universal">universal</option>}
          </select>
          {streaming && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('chat.streaming')}</span>}
        </div>

        <div className="chat-messages">
          {messages.length === 0 ? (
            <EmptyState
              title={t('chat.emptyTitle')}
              description={t('chat.emptyDesc')}
              actionLabel={t('chat.emptyCta')}
              actionTo="/marketplace"
            />
          ) : (
            messages.map(renderBubble)
          )}
          <div ref={bottomRef} />
        </div>

        <div className="chat-examples">
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{t('chat.tryExamples')}</span>
          {EXAMPLE_PROMPTS.map((ex) => (
            <button key={ex} type="button" className="chat-example-chip" onClick={() => sendMessage(ex)}>
              {ex}
            </button>
          ))}
        </div>

        <div className="chat-composer">
          <textarea
            ref={textareaRef}
            className="input"
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder={t('chat.placeholder')}
            disabled={streaming}
          />
          <button type="button" className="btn btn-primary" onClick={() => sendMessage()} disabled={streaming}>
            {t('common.send')}
          </button>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .chat-toolbar .mobile-toggle { display: inline-flex !important; }
        }
      `}</style>
    </div>
  );
}
