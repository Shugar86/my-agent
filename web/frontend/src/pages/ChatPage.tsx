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
  type Agent,
  type ChatSession,
} from '../api/appClient';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const [searchParams] = useSearchParams();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentId, setAgentId] = useState(searchParams.get('agent') || 'universal');
  const [threads, setThreads] = useState<ChatSession[]>([]);
  const [activeThread, setActiveThread] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

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
  }, [searchParams]);

  useEffect(() => {
    if (!activeThread) {
      setMessages([]);
      return;
    }
    getChatMessages(activeThread)
      .then((msgs) => setMessages(msgs.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))))
      .catch(() => setMessages([]));
  }, [activeThread]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleRunCommand = async (text: string): Promise<string | null> => {
    const match = text.match(/^\/run\s+(.+)/i);
    if (!match) return null;
    const query = match[1].trim();
    const workflows = await listWorkflows();
    const wf = workflows.find((w) => w.id === query || w.name.toLowerCase() === query.toLowerCase())
      || workflows.find((w) => w.name.toLowerCase().includes(query.toLowerCase()));
    if (!wf) return `Workflow not found: ${query}`;
    try {
      const result = await runWorkflowById(wf.id, { chat_trigger: true }) as { success: boolean; run_id?: string; error?: string };
      return result.success
        ? `Workflow "${wf.name}" completed (run: ${result.run_id})`
        : `Workflow failed: ${result.error || 'unknown error'}`;
    } catch {
      return `Failed to run workflow "${query}"`;
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || streaming) return;
    const userMsg = input.trim();
    setInput('');
    setStreaming(true);

    let threadId = activeThread;
    if (!threadId) {
      const created = await createChatSession(userMsg.slice(0, 40), agentId);
      threadId = created.id;
      setActiveThread(threadId);
      loadThreads();
    }

    setMessages((prev) => [...prev, { role: 'user', content: userMsg }, { role: 'assistant', content: '' }]);

    const runResult = await handleRunCommand(userMsg);
    if (runResult !== null) {
      setMessages((prev) => {
        const msgs = [...prev];
        msgs[msgs.length - 1] = { role: 'assistant', content: runResult };
        return msgs;
      });
      setStreaming(false);
      return;
    }

    let assistantText = '';
    try {
      await streamChat(userMsg, agentId, (event) => {
        if (event.type === 'token' && typeof event.content === 'string') {
          assistantText += event.content;
          setMessages((prev) => {
            const msgs = [...prev];
            msgs[msgs.length - 1] = { role: 'assistant', content: assistantText };
            return msgs;
          });
        }
      }, threadId);
      loadThreads();
    } catch {
      setMessages((prev) => {
        const msgs = [...prev];
        msgs[msgs.length - 1] = { role: 'assistant', content: 'Error: failed to get response' };
        return msgs;
      });
    }
    setStreaming(false);
  };

  const newThread = async () => {
    const created = await createChatSession('New chat', agentId);
    setThreads((prev) => [created, ...prev]);
    setActiveThread(created.id);
    setMessages([]);
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 0px)' }}>
      <aside style={{ width: 200, borderRight: '1px solid var(--border)', padding: 12, overflowY: 'auto' }}>
        <button className="btn btn-primary" style={{ width: '100%', marginBottom: 12 }} onClick={newThread}>+ New chat</button>
        {threads.map((t) => (
          <button
            key={t.id}
            className="btn"
            style={{
              width: '100%', marginBottom: 6, textAlign: 'left',
              background: t.id === activeThread ? 'var(--bg-tertiary)' : undefined,
            }}
            onClick={() => setActiveThread(t.id)}
          >
            {t.title || 'New chat'}
          </button>
        ))}
      </aside>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 12, alignItems: 'center' }}>
          <select className="input" style={{ width: 'auto' }} value={agentId} onChange={(e) => setAgentId(e.target.value)}>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>{a.name || a.id}</option>
            ))}
            {agents.length === 0 && <option value="universal">universal</option>}
          </select>
          {streaming && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Streaming...</span>}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
          {messages.length === 0 && (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: 40 }}>
              Start a conversation or type /run &lt;workflow name&gt; to trigger a workflow
            </p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                marginBottom: 16, padding: 12, borderRadius: 8, maxWidth: '80%',
                marginLeft: m.role === 'user' ? 'auto' : 0,
                background: m.role === 'user' ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
                border: '1px solid var(--border)',
              }}
            >
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{m.role}</div>
              <div style={{ whiteSpace: 'pre-wrap', fontSize: 14 }}>{m.content || (streaming && i === messages.length - 1 ? '...' : '')}</div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        <div style={{ padding: 16, borderTop: '1px solid var(--border)', display: 'flex', gap: 8 }}>
          <input
            className="input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Message or /run workflow-name..."
            disabled={streaming}
          />
          <button className="btn btn-primary" onClick={sendMessage} disabled={streaming}>Send</button>
        </div>
      </div>
    </div>
  );
}
