export interface WorkflowNode {
  id: string;
  type: string;
  config: Record<string, unknown>;
  position?: { x: number; y: number };
}

export interface WorkflowEdge {
  from: string;
  to: string;
  label?: string;
}

export interface WorkflowDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Workflow {
  id: string;
  name: string;
  definition: WorkflowDefinition;
  status: string;
  owner_id?: string;
  webhook_token?: string;
}

export const NODE_TYPES = [
  { type: 'trigger.webhook', label: 'Webhook Trigger', category: 'trigger', color: '#238636', icon: 'WB' },
  { type: 'trigger.schedule', label: 'Schedule', category: 'trigger', color: '#238636', icon: 'SC' },
  { type: 'trigger.telegram', label: 'Telegram', category: 'trigger', color: '#238636', icon: 'TG' },
  { type: 'trigger.email', label: 'Email', category: 'trigger', color: '#238636', icon: 'EM' },
  { type: 'agent.skill', label: 'Agent / Skill', category: 'agent', color: '#58a6ff', icon: 'AI' },
  { type: 'condition', label: 'Condition', category: 'logic', color: '#d29922', icon: 'IF' },
  { type: 'util.set', label: 'Set Variables', category: 'logic', color: '#d29922', icon: 'SE' },
  { type: 'util.merge', label: 'Merge Inputs', category: 'logic', color: '#d29922', icon: 'MR' },
  { type: 'util.wait', label: 'Wait', category: 'logic', color: '#d29922', icon: 'WT' },
  { type: 'util.code', label: 'Code (Python)', category: 'logic', color: '#d29922', icon: 'PY' },
  { type: 'action.telegram', label: 'Send Telegram', category: 'action', color: '#8957e5', icon: 'TG' },
  { type: 'action.slack', label: 'Send Slack', category: 'action', color: '#8957e5', icon: 'SL' },
  { type: 'action.gmail_send', label: 'Send Gmail', category: 'action', color: '#8957e5', icon: 'GM' },
  { type: 'action.sheets_write', label: 'Write Sheets', category: 'action', color: '#8957e5', icon: 'GS' },
  { type: 'action.notion_page', label: 'Notion Page', category: 'action', color: '#8957e5', icon: 'NT' },
  { type: 'action.notion_db_update', label: 'Notion DB Update', category: 'action', color: '#8957e5', icon: 'ND' },
  { type: 'action.http', label: 'HTTP Request', category: 'action', color: '#8957e5', icon: 'HT' },
  { type: 'action.webhook', label: 'POST Webhook', category: 'action', color: '#8957e5', icon: 'WH' },
  { type: 'action.n8n_webhook', label: 'n8n Webhook', category: 'action', color: '#ea4b71', icon: 'N8' },
];

export const NODE_CATEGORIES: Array<{ id: string; label: string; color: string }> = [
  { id: 'trigger', label: 'Triggers', color: '#238636' },
  { id: 'agent', label: 'AI / Agents', color: '#58a6ff' },
  { id: 'logic', label: 'Logic & Data', color: '#d29922' },
  { id: 'action', label: 'Actions & Integrations', color: '#8957e5' },
];
