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
  { type: 'trigger.webhook', label: 'Webhook Trigger', category: 'trigger', color: '#238636' },
  { type: 'trigger.schedule', label: 'Schedule', category: 'trigger', color: '#238636' },
  { type: 'trigger.telegram', label: 'Telegram', category: 'trigger', color: '#238636' },
  { type: 'trigger.email', label: 'Email', category: 'trigger', color: '#238636' },
  { type: 'agent.skill', label: 'Agent / Skill', category: 'agent', color: '#58a6ff' },
  { type: 'condition', label: 'Condition', category: 'logic', color: '#d29922' },
  { type: 'action.telegram', label: 'Send Telegram', category: 'action', color: '#8957e5' },
  { type: 'action.slack', label: 'Send Slack', category: 'action', color: '#8957e5' },
  { type: 'action.gmail_send', label: 'Send Gmail', category: 'action', color: '#8957e5' },
  { type: 'action.sheets_write', label: 'Write Sheets', category: 'action', color: '#8957e5' },
  { type: 'action.notion_page', label: 'Notion Page', category: 'action', color: '#8957e5' },
];
