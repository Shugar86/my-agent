import type { DemoRunResult } from '../api/appClient';
import { DEFAULT_DEMO_NODE_ORDER } from './demoNodeLabels';

export interface OfflinePlaygroundRun {
  workflow_id: string;
  run_id: string;
  mode: 'mock';
  artifact_url: string;
  logs: Array<{ node_id: string; event: string; detail?: unknown }>;
  status: 'running' | 'success';
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
  count: number,
): OfflinePlaygroundRun['logs'] {
  return DEFAULT_DEMO_NODE_ORDER.slice(0, count).map((node_id) => ({
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
  options?: { animate?: boolean },
): OfflinePlaygroundRun {
  const animate = options?.animate ?? true;
  return {
    workflow_id: 'offline-demo',
    run_id: `offline-${Date.now()}`,
    mode: 'mock',
    status: animate ? 'running' : 'success',
    artifact_url: OFFLINE_ARTIFACTS[preset],
    logs: animate ? [] : buildOfflineLogs(target, ourCompany, preset, DEFAULT_DEMO_NODE_ORDER.length),
  };
}

/** Append next offline step log or mark run complete. */
export function advanceOfflineDemoRun(
  run: OfflinePlaygroundRun,
  target: string,
  ourCompany: string,
  preset: 'competitor' | 'beauty' | 'lead',
): OfflinePlaygroundRun {
  const nextIndex = run.logs.length;
  if (nextIndex >= DEFAULT_DEMO_NODE_ORDER.length) {
    return { ...run, status: 'success' };
  }
  return {
    ...run,
    logs: buildOfflineLogs(target, ourCompany, preset, nextIndex + 1),
    status: nextIndex + 1 >= DEFAULT_DEMO_NODE_ORDER.length ? 'success' : 'running',
  };
}

export function toDemoRunResult(offline: OfflinePlaygroundRun): DemoRunResult {
  return {
    mode: offline.mode,
    workflow_id: offline.workflow_id,
    run_id: offline.run_id,
    artifact_url: offline.artifact_url,
  };
}
