const API = '';

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${url}`, options);
  if (!res.ok) throw new Error(`Request failed: ${url}`);
  return res.json();
}

export interface Agent {
  id: string;
  name: string;
  role?: string;
  skills?: string[];
  tools?: string[];
  memory?: { enabled: boolean };
  model?: Record<string, unknown>;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  installs: number;
  rating_avg: number;
  rating_count: number;
}

export async function listAgents(): Promise<Agent[]> {
  return fetchJson<Agent[]>('/api/agents');
}

export async function getAgent(id: string): Promise<Agent> {
  return fetchJson<Agent>(`/api/agents/${id}`);
}

export async function saveAgent(config: Record<string, unknown>): Promise<{ id: string }> {
  const id = config.id as string | undefined;
  if (id) {
    await fetchJson(`/api/agents/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    return { id };
  }
  return fetchJson('/api/agents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
}

export async function listTemplates(category?: string, sort = 'popular'): Promise<Template[]> {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  params.set('sort', sort);
  const data = await fetchJson<{ templates: Template[] }>(`/api/workflow-templates?${params}`);
  return data.templates;
}

export async function installTemplate(id: string): Promise<{ workflow: { id: string } }> {
  return fetchJson(`/api/workflow-templates/${id}/install`, { method: 'POST' });
}

export async function rateTemplate(id: string, score: number): Promise<void> {
  await fetchJson(`/api/workflow-templates/${id}/rate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ score }),
  });
}

export async function getHealth(): Promise<Record<string, unknown>> {
  return fetchJson('/api/health');
}

export { listWorkflows } from './workflowClient';

export async function getMe(): Promise<{ id: string; username: string; role: string }> {
  return fetchJson('/api/me');
}

export async function publishTemplate(body: {
  name: string;
  description: string;
  category: string;
  definition: Record<string, unknown>;
  tags?: string[];
}): Promise<void> {
  await fetchJson('/api/workflow-templates', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export interface ChatSession {
  id: string;
  title: string;
  message_count?: number;
}

export async function listChatSessions(): Promise<ChatSession[]> {
  const data = await fetchJson<{ sessions: ChatSession[] }>('/api/sessions');
  return data.sessions;
}

export async function createChatSession(title = 'New chat', agentId = 'universal'): Promise<ChatSession> {
  return fetchJson('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, agent_id: agentId }),
  });
}

export async function getChatMessages(sessionId: string): Promise<Array<{ role: string; content: string }>> {
  const data = await fetchJson<{ messages: Array<{ role: string; content: string }> }>(
    `/api/sessions/${sessionId}/messages`,
  );
  return data.messages;
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await fetchJson(`/api/sessions/${sessionId}`, { method: 'DELETE' });
}

export async function runWorkflowById(id: string, payload: Record<string, unknown> = {}): Promise<unknown> {
  const res = await fetch(`/api/workflows/${id}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payload }),
  });
  if (!res.ok) throw new Error('Run failed');
  return res.json();
}

export async function streamChat(
  message: string,
  agentId: string,
  onEvent: (event: Record<string, unknown>) => void,
  sessionId?: string,
): Promise<string | undefined> {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, agent_id: agentId, session_id: sessionId }),
  });
  if (!res.ok || !res.body) throw new Error('Stream failed');
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let resolvedSessionId: string | undefined = sessionId;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === 'session' && event.session_id) {
            resolvedSessionId = String(event.session_id);
          }
          onEvent(event);
        } catch { /* skip malformed */ }
      }
    }
  }
  return resolvedSessionId;
}
