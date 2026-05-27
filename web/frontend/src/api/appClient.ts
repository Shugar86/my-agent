const API = '';

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, url: string) {
    super(`Request failed: ${url}`);
    this.status = status;
  }
}

export async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${url}`, options);
  if (!res.ok) throw new ApiError(res.status, url);
  const text = await res.text();
  if (!text) return {} as T;
  return JSON.parse(text) as T;
}

export interface Agent {
  id: string;
  name: string;
  role?: string;
  icon?: string;
  description?: string;
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
  definition?: { nodes: Array<{ id: string; type: string; position?: { x: number; y: number } }>; edges: Array<{ from: string; to: string; label?: string }> };
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

export async function deleteAgent(id: string): Promise<void> {
  await fetchJson(`/api/agents/${id}`, { method: 'DELETE' });
}

export async function duplicateAgent(id: string): Promise<{ id: string }> {
  return fetchJson(`/api/agents/${id}/duplicate`, { method: 'POST' });
}

export interface KnowledgeDoc {
  id: string;
  source: string;
  preview: string;
  created_at?: string;
}

export async function uploadKnowledge(content: string, source = ''): Promise<{ id: string }> {
  return fetchJson('/api/knowledge/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, source }),
  });
}

export async function searchKnowledge(query: string, nResults = 5): Promise<Array<{ content: string; source: string; score: number }>> {
  const data = await fetchJson<{ results: Array<{ content: string; source: string; score: number }> }>(
    '/api/knowledge/search',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, n_results: nResults }),
    },
  );
  return data.results || [];
}

export async function listKnowledgeDocs(): Promise<KnowledgeDoc[]> {
  const data = await fetchJson<{ documents: KnowledgeDoc[] }>('/api/knowledge/list');
  return data.documents || [];
}

export async function deleteKnowledgeDoc(docId: string): Promise<void> {
  await fetchJson(`/api/knowledge/delete/${docId}`, { method: 'DELETE' });
}

export interface McpServer {
  name: string;
  enabled: boolean;
  connected: boolean;
  tools_count: number;
  command?: string;
}

export async function listMcpServers(): Promise<McpServer[]> {
  const data = await fetchJson<{ servers: McpServer[] }>('/api/mcp/list');
  return data.servers || [];
}

export async function startMcpServer(name: string): Promise<{ success: boolean; tools?: number; error?: string }> {
  return fetchJson(`/api/mcp/start/${encodeURIComponent(name)}`, { method: 'POST' });
}

export async function stopMcpServer(name: string): Promise<{ success: boolean; error?: string }> {
  return fetchJson(`/api/mcp/stop/${encodeURIComponent(name)}`, { method: 'POST' });
}

export async function startAllMcp(): Promise<unknown> {
  return fetchJson('/api/mcp/start-all', { method: 'POST' });
}

export async function stopAllMcp(): Promise<unknown> {
  return fetchJson('/api/mcp/stop-all', { method: 'POST' });
}

export async function submitFeedback(body: {
  session_id: string;
  message_id: string;
  query: string;
  response: string;
  rating: number;
  agent_id?: string;
}): Promise<void> {
  await fetchJson('/api/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export async function getAppConfig(): Promise<{ model?: { primary?: string; api_key?: string } }> {
  return fetchJson('/api/config');
}

export async function saveAppConfig(config: { model?: { primary?: string; api_key?: string } }): Promise<void> {
  await fetchJson('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
}

export async function logUxEvent(event: string, metadata: Record<string, unknown> = {}): Promise<void> {
  try {
    await fetch('/api/usage/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: event, metadata }),
    });
  } catch { /* best-effort */ }
}

export async function listTemplates(
  category?: string,
  sort = 'popular',
  search?: string,
): Promise<Template[]> {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  params.set('sort', sort);
  if (search) params.set('q', search);
  const data = await fetchJson<{ templates: Template[] }>(`/api/workflow-templates?${params}`);
  return data.templates;
}

export async function getTemplate(id: string): Promise<Template> {
  return fetchJson<Template>(`/api/workflow-templates/${id}`);
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

export async function demoRunTemplate(id: string): Promise<{
  success: boolean;
  run_id: string;
  status: string;
  mode: string;
  logs: Array<{ node_id: string; event: string; detail?: unknown }>;
  message?: string;
}> {
  return fetchJson(`/api/workflow-templates/${id}/demo-run`, { method: 'POST' });
}

export interface BillingPlan {
  workspace_id?: string;
  workspace_name?: string;
  plan: string;
  label: string;
  workflow_runs_used: number;
  workflow_runs_limit: number | null;
  allowed: boolean;
}

export async function getBillingPlan(): Promise<BillingPlan> {
  return fetchJson('/api/billing/plan');
}

export interface ApiKeyEntry {
  name: string;
  masked?: string;
}

export async function listApiKeys(): Promise<{ keys: ApiKeyEntry[]; count: number }> {
  return fetchJson('/api/keys');
}

export async function saveApiKey(name: string, value: string): Promise<void> {
  await fetchJson('/api/keys', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, value }),
  });
}

export async function deleteApiKey(name: string): Promise<void> {
  await fetchJson(`/api/keys/${encodeURIComponent(name)}`, { method: 'DELETE' });
}

export interface ScheduleJob {
  id: string;
  description?: string;
  next_run_time?: string | null;
  last_run_time?: string | null;
  last_run_status?: string | null;
  paused?: boolean;
  trigger?: string;
}

export async function listScheduleJobs(): Promise<{ jobs: ScheduleJob[] }> {
  return fetchJson('/api/schedule');
}

export async function pauseScheduleJob(jobId: string): Promise<{ success: boolean }> {
  return fetchJson(`/api/schedule/${encodeURIComponent(jobId)}/pause`, { method: 'POST' });
}

export async function resumeScheduleJob(jobId: string): Promise<{ success: boolean }> {
  return fetchJson(`/api/schedule/${encodeURIComponent(jobId)}/resume`, { method: 'POST' });
}

export async function getHealth(): Promise<Record<string, unknown>> {
  return fetchJson('/api/health');
}

export { listWorkflows } from './workflowClient';

export async function getMe(): Promise<MeUser> {
  return fetchJson('/api/me');
}

export interface MeUser {
  id: string;
  username: string;
  role: string;
  email?: string;
  auth_provider?: string;
  workspace_id?: string;
  team_role?: string;
  teams?: Team[];
}

export interface Team {
  id: string;
  name: string;
  slug: string;
  plan: string;
  member_role?: string;
}

export interface UsageSummary {
  team_id: string;
  period_days: number;
  total_tokens: number;
  total_cost_usd: number;
  event_count: number;
  workflow_runs: number;
  daily: Array<{ day: string; tokens: number; events: number }>;
  top_workflows: Array<{ workflow_id: string; runs: number }>;
}

export async function listTeams(): Promise<{ teams: Team[]; active_team_id?: string }> {
  return fetchJson('/api/teams');
}

export async function createTeam(name: string): Promise<{ team: Team }> {
  return fetchJson('/api/teams', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
}

export async function setActiveTeam(teamId: string): Promise<void> {
  await fetchJson('/api/teams/active', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ team_id: teamId }),
  });
}

export async function listTeamMembers(teamId: string): Promise<Array<{ user_id: string; role: string }>> {
  const data = await fetchJson<{ members: Array<{ user_id: string; role: string }> }>(`/api/teams/${teamId}/members`);
  return data.members;
}

export async function inviteTeamMember(teamId: string, email: string): Promise<{ accept_url: string }> {
  const data = await fetchJson<{ accept_url: string }>(`/api/teams/${teamId}/invite`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, role: 'member' }),
  });
  return data;
}

export async function acceptInvite(token: string): Promise<void> {
  await fetchJson('/api/teams/accept-invite', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  });
}

export async function getUsageSummary(period: '7d' | '30d' = '7d'): Promise<UsageSummary> {
  return fetchJson(`/api/usage/summary?period=${period}`);
}

export async function listUsers(): Promise<Array<{ id: string; username: string; role: string; email?: string }>> {
  const data = await fetchJson<{ users: Array<{ id: string; username: string; role: string; email?: string }> }>('/api/users');
  return data.users;
}

export async function completeOnboarding(): Promise<void> {
  await fetchJson('/api/onboarding/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ complete: true }),
  });
}

export async function getIntegrationAuthUrl(provider: string): Promise<{ auth_url: string }> {
  return fetchJson(`/api/integrations/${provider}/auth`);
}

export interface IntegrationField {
  name: string;
  label: string;
  type: string;
  required: boolean;
  help?: string;
}

export interface Integration {
  provider: string;
  name: string;
  category: string;
  description: string;
  auth_method: string;
  actions: string[];
  fields: IntegrationField[];
  docs_url?: string;
  configured: boolean;
}

export async function listIntegrations(): Promise<Integration[]> {
  const data = await fetchJson<{ integrations: Integration[] }>('/api/integrations');
  return data.integrations;
}

export async function saveIntegrationCredentials(provider: string, credentials: Record<string, string>): Promise<void> {
  await fetchJson('/api/integrations/credentials', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, credentials }),
  });
}

export async function testIntegration(provider: string): Promise<{ success: boolean; info?: unknown; error?: string }> {
  return fetchJson(`/api/integrations/${provider}/test`, { method: 'POST' });
}

export async function deleteIntegration(provider: string): Promise<void> {
  await fetchJson(`/api/integrations/credentials/${provider}`, { method: 'DELETE' });
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

export interface DemoRunResult {
  mode: 'mock' | 'real';
  workflow_id: string;
  run_id: string;
  node_order?: string[];
  expected_duration_ms?: number;
  artifact_url: string;
  summary?: { total_duration_ms?: number; total_duration_human?: string; tokens_used?: number; estimated_cost_usd?: number };
}

export async function startPublicDemoRun(
  target = 'Notion',
  ourCompany = 'Linear',
  preset: 'competitor' | 'beauty' | 'lead' = 'competitor',
): Promise<DemoRunResult> {
  const res = await fetch('/api/demo/public/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target, our_company: ourCompany, real: false, preset }),
  });
  if (!res.ok) throw new Error('Public demo run failed');
  return res.json();
}

export async function getPublicDemoRun(
  runId: string,
  preset: 'competitor' | 'beauty' | 'lead' = 'competitor',
): Promise<{ status: string; node_order?: string[]; logs: Array<{ node_id: string; event: string; detail?: unknown }> }> {
  const res = await fetch(`/api/demo/public/runs/${runId}?preset=${preset}`);
  if (!res.ok) throw new Error('Public demo poll failed');
  return res.json();
}

export async function startDemoRun(
  target = 'Notion',
  ourCompany = 'Linear',
  real = false,
  preset: 'competitor' | 'beauty' | 'lead' = 'competitor',
): Promise<DemoRunResult> {
  const res = await fetch('/api/demo/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target, our_company: ourCompany, real, preset }),
  });
  if (!res.ok) throw new Error('Demo run failed');
  return res.json();
}

export async function getDemoSample(
  preset: 'competitor' | 'beauty' | 'lead' = 'competitor',
): Promise<{ summary: Record<string, unknown>; node_order: string[]; default_payload: Record<string, string> }> {
  const res = await fetch(`/api/demo/sample?preset=${preset}`);
  if (!res.ok) throw new Error('Demo sample fetch failed');
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
