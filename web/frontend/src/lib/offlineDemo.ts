import type { DemoRunResult } from '../api/appClient';
import { DEFAULT_DEMO_NODE_ORDER } from './demoNodeLabels';

export interface OfflinePlaygroundRun {
  workflow_id: string;
  run_id: string;
  mode: 'mock';
  artifact_url: string;
  logs: Array<{ node_id: string; event: string; detail?: unknown }>;
  status: 'running' | 'success';
  node_order: string[];
}

const OFFLINE_ARTIFACTS: Record<'competitor' | 'beauty' | 'lead', string> = {
  competitor: '/api/demo/artifact/competitor_brief_notion_vs_linear.docx',
  beauty: '/api/demo/artifact/beauty_consultant_brief.docx',
  lead: '/api/demo/artifact/lead_qualifier_brief.docx',
};

/** Step interval for offline replay (~21s total for 7 nodes). */
export const OFFLINE_DEMO_STEP_MS = 3000;

function buildOfflineLogs(
  target: string,
  ourCompany: string,
  preset: 'competitor' | 'beauty' | 'lead',
  nodeOrder: string[],
  count: number,
): OfflinePlaygroundRun['logs'] {
  return nodeOrder.slice(0, count).map((node_id) => ({
    node_id,
    event: 'completed',
    detail: { target, our_company: ourCompany, preset },
  }));
}

/** Prerecorded demo state when `/api/demo/run` is unavailable. */
export function buildOfflineDemoRun(
  target: string,
  ourCompany: string,
  preset: 'competitor' | 'beauty' | 'lead' = 'competitor',
  options?: { animate?: boolean; nodeOrder?: string[] },
): OfflinePlaygroundRun {
  const animate = options?.animate ?? true;
  const nodeOrder = options?.nodeOrder?.length ? options.nodeOrder : DEFAULT_DEMO_NODE_ORDER;
  return {
    workflow_id: 'offline-demo',
    run_id: `offline-${Date.now()}`,
    mode: 'mock',
    status: animate ? 'running' : 'success',
    artifact_url: OFFLINE_ARTIFACTS[preset],
    node_order: nodeOrder,
    logs: animate ? [] : buildOfflineLogs(target, ourCompany, preset, nodeOrder, nodeOrder.length),
  };
}

/** Append next offline step log or mark run complete. */
export function advanceOfflineDemoRun(
  run: OfflinePlaygroundRun,
  target: string,
  ourCompany: string,
  preset: 'competitor' | 'beauty' | 'lead',
): OfflinePlaygroundRun {
  const nodeOrder = run.node_order.length ? run.node_order : DEFAULT_DEMO_NODE_ORDER;
  const nextIndex = run.logs.length;
  if (nextIndex >= nodeOrder.length) {
    return { ...run, status: 'success' };
  }
  return {
    ...run,
    logs: buildOfflineLogs(target, ourCompany, preset, nodeOrder, nextIndex + 1),
    status: nextIndex + 1 >= nodeOrder.length ? 'success' : 'running',
  };
}

export function toDemoRunResult(offline: OfflinePlaygroundRun): DemoRunResult {
  return {
    mode: offline.mode,
    workflow_id: offline.workflow_id,
    run_id: offline.run_id,
    artifact_url: offline.artifact_url,
    node_order: offline.node_order,
  };
}
