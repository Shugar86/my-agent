import type { Workflow, WorkflowDefinition } from '../types/workflow';

const API = '';

export async function listWorkflows(): Promise<Workflow[]> {
  const res = await fetch(`${API}/api/workflows`);
  if (!res.ok) throw new Error('Failed to load workflows');
  const data = await res.json();
  return data.workflows;
}

export async function getWorkflow(id: string): Promise<Workflow> {
  const res = await fetch(`${API}/api/workflows/${id}`);
  if (!res.ok) throw new Error('Workflow not found');
  return res.json();
}

export async function createWorkflow(name: string, definition: WorkflowDefinition, status = 'draft'): Promise<Workflow> {
  const res = await fetch(`${API}/api/workflows`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, definition, status }),
  });
  if (!res.ok) throw new Error('Failed to create workflow');
  return res.json();
}

export async function updateWorkflow(id: string, name: string, definition: WorkflowDefinition, status?: string): Promise<Workflow> {
  const res = await fetch(`${API}/api/workflows/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, definition, status }),
  });
  if (!res.ok) throw new Error('Failed to update workflow');
  return res.json();
}

export async function runWorkflow(id: string, payload: Record<string, unknown> = {}): Promise<unknown> {
  const res = await fetch(`${API}/api/workflows/${id}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payload }),
  });
  if (!res.ok) throw new Error('Run failed');
  return res.json();
}

export async function deleteWorkflow(id: string): Promise<void> {
  const res = await fetch(`${API}/api/workflows/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Delete failed');
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  status: string;
  started_at: string;
  finished_at?: string;
  log_json?: string;
  logs?: Array<{ node_id: string; event: string; detail?: unknown }>;
}

export async function listRuns(workflowId: string): Promise<WorkflowRun[]> {
  const res = await fetch(`${API}/api/workflows/${workflowId}/runs`);
  if (!res.ok) throw new Error('Failed to load runs');
  const data = await res.json();
  return data.runs.map((r: WorkflowRun & { log_json?: string }) => ({
    ...r,
    logs: r.log_json ? JSON.parse(r.log_json) : r.logs || [],
  }));
}

export async function getRun(workflowId: string, runId: string): Promise<WorkflowRun> {
  const res = await fetch(`${API}/api/workflows/${workflowId}/runs/${runId}`);
  if (!res.ok) throw new Error('Failed to load run');
  const r = await res.json();
  return { ...r, logs: r.logs || [] };
}

export async function validateWorkflow(definition: WorkflowDefinition): Promise<{
  valid: boolean;
  errors: string[];
  warnings: string[];
}> {
  const res = await fetch(`${API}/api/workflows/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ definition }),
  });
  if (!res.ok) throw new Error('Validation failed');
  return res.json();
}
