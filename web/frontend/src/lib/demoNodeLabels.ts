/** Human-readable labels for Competitor Intelligence demo nodes. */
export const DEMO_NODE_LABELS: Record<string, string> = {
  trg: 'Webhook-триггер',
  r1: 'Research: продукт и pricing',
  r2: 'Research: новости и funding',
  merge: 'Объединение данных',
  an: 'SWOT + 3 actions',
  doc: 'Генерация DOCX',
  n8n: 'Триггер n8n',
  a1: 'AI-агент',
  x1: 'Ответ / уведомление',
  x2: 'Запись в Sheets',
  c1: 'Условие (BANT score)',
};

export const DEFAULT_DEMO_NODE_ORDER = ['trg', 'r1', 'r2', 'merge', 'an', 'doc', 'n8n'];

export interface DemoPreset {
  id: string;
  label: string;
  target: string;
  our_company: string;
}

export const DEFAULT_DEMO_PRESETS: DemoPreset[] = [
  { id: 'notion-linear', label: 'Notion vs Linear', target: 'Notion', our_company: 'Linear' },
  { id: 'slack-teams', label: 'Slack vs Teams', target: 'Slack', our_company: 'Teams' },
  { id: 'figma-sketch', label: 'Figma vs Sketch', target: 'Figma', our_company: 'Sketch' },
];
