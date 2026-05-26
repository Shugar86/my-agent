import { DEMO_NODE_LABELS } from '../../lib/demoNodeLabels';

interface LogEntry {
  node_id: string;
  event: string;
  detail?: unknown;
}

interface DemoStepperProps {
  nodeOrder: string[];
  nodeLabels?: Record<string, string>;
  logs: LogEntry[];
  status: string;
}

function getLogMessage(log: LogEntry): string {
  const d = log.detail;
  if (typeof d === 'string') return d;
  if (d && typeof d === 'object') {
    const obj = d as Record<string, unknown>;
    if (typeof obj.message === 'string') return obj.message;
    const output = obj.output as Record<string, unknown> | undefined;
    if (output && typeof output.summary === 'string') {
      return `${output.summary.slice(0, 80)}…`;
    }
  }
  return '';
}

/** Vertical stepper for demo workflow execution (ported from showcase.js). */
export default function DemoStepper({ nodeOrder, nodeLabels, logs, status }: DemoStepperProps) {
  const labels = nodeLabels ?? DEMO_NODE_LABELS;
  const completed = new Set<string>();
  let running: string | null = null;
  const logByNode: Record<string, LogEntry> = {};

  for (const log of logs) {
    if (log.node_id) logByNode[log.node_id] = log;
    if (log.event === 'completed' && log.node_id) completed.add(log.node_id);
    if (log.event === 'started' && log.node_id && !completed.has(log.node_id)) {
      running = log.node_id;
    }
  }
  if (status === 'success') nodeOrder.forEach((id) => completed.add(id));

  return (
    <div className="demo-stepper">
      {nodeOrder.map((id) => {
        const label = labels[id] || DEMO_NODE_LABELS[id] || id;
        let stepClass = 'demo-step';
        let marker = '○';
        if (completed.has(id)) {
          stepClass += ' demo-step--done';
          marker = '✓';
        } else if (running === id) {
          stepClass += ' demo-step--running';
          marker = '●';
        }
        const log = logByNode[id];
        const snippet = log ? getLogMessage(log) : '';
        return (
          <div key={id} className={stepClass} data-node={id}>
            <div className="demo-step-marker">{marker}</div>
            <div>
              <div className="demo-step-label">{label}</div>
              {snippet && <div className="demo-step-log">{snippet}</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
