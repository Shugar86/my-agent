import type { DemoRunResult } from '../api/appClient';
import { DEFAULT_DEMO_NODE_ORDER } from './demoNodeLabels';

export interface OfflinePlaygroundRun {
  workflow_id: string;
  run_id: string;
  mode: 'mock';
  artifact_url: string;
  logs: Array<{ node_id: string; event: string; detail?: unknown }>;
  status: 'success';
}

/** Prerecorded demo state when `/api/demo/run` is unavailable. */
export function buildOfflineDemoRun(
  target: string,
  ourCompany: string,
  preset: 'competitor' | 'beauty' | 'lead' = 'competitor',
): OfflinePlaygroundRun {
  const artifacts: Record<string, string> = {
    competitor: '/api/demo/artifact/competitor_brief_notion_vs_linear.docx',
    beauty: '/api/demo/artifact/beauty_consultant_brief.docx',
    lead: '/api/demo/artifact/lead_qualifier_brief.docx',
  };
  const logs = DEFAULT_DEMO_NODE_ORDER.map((node_id) => ({
    node_id,
    event: 'completed',
    detail: { target, our_company: ourCompany, preset },
  }));
  return {
    workflow_id: 'offline-demo',
    run_id: `offline-${Date.now()}`,
    mode: 'mock',
    status: 'success',
    artifact_url: artifacts[preset],
    logs,
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
