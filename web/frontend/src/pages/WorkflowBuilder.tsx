import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import WorkflowNodeComponent from '../components/nodes/WorkflowNodeComponent';
import ExecutionTimeline from '../components/ExecutionTimeline';
import { NODE_TYPES, NODE_CATEGORIES, type WorkflowDefinition } from '../types/workflow';
import {
  getWorkflow,
  updateWorkflow,
  runWorkflow,
  createWorkflow,
  listRuns,
  validateWorkflow,
  getRun,
  type WorkflowRun,
} from '../api/workflowClient';
import { t, type I18nKey } from '../i18n';

function builderNodeLabel(type: string): string {
  const key = `builder.nodes.${type.replace(/\./g, '_')}` as I18nKey;
  const label = t(key);
  return label === key ? type : label;
}

function builderCategoryLabel(id: string): string {
  const key = `builder.categories.${id}` as I18nKey;
  const label = t(key);
  return label === key ? id : label;
}

const nodeTypes = { workflowNode: WorkflowNodeComponent };

const EDGE_STROKE: Record<string, string> = {
  true: '#238636',
  false: '#f85149',
  error: '#f85149',
};

function edgeStyle(label?: string | null): { stroke: string; strokeDasharray?: string } {
  const key = (label || '').toLowerCase();
  const stroke = EDGE_STROKE[key] || '#58a6ff';
  return key === 'error' ? { stroke, strokeDasharray: '6 4' } : { stroke };
}

function defToFlow(definition: WorkflowDefinition): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = definition.nodes.map((n, i) => ({
    id: n.id,
    type: 'workflowNode',
    position: n.position || { x: 100 + (i % 3) * 240, y: 80 + Math.floor(i / 3) * 140 },
    data: { nodeType: n.type, nodeId: n.id, config: n.config },
  }));
  const edges: Edge[] = definition.edges.map((e, i) => ({
    id: `e${i}`,
    source: e.from,
    sourceHandle: (e.label || '').toLowerCase() === 'error' ? 'error' : 'success',
    target: e.to,
    label: e.label,
    animated: true,
    style: edgeStyle(e.label),
  }));
  return { nodes, edges };
}

function flowToDef(nodes: Node[], edges: Edge[]): WorkflowDefinition {
  return {
    nodes: nodes.map((n) => ({
      id: n.id,
      type: String(n.data.nodeType),
      config: (n.data.config as Record<string, unknown>) || {},
      position: n.position,
    })),
    edges: edges.map((e) => ({
      from: e.source,
      to: e.target,
      ...(e.label ? { label: String(e.label) } : {}),
    })),
  };
}

export default function WorkflowBuilder() {
  const { workflowId: paramId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const workflowId = paramId === 'new' ? undefined : paramId;
  const demoRunHandled = useRef<string | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [name, setName] = useState(() => t('builder.newWorkflowName'));
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [status, setStatus] = useState('');
  const [wfStatus, setWfStatus] = useState<'draft' | 'active'>('draft');
  const [currentId, setCurrentId] = useState(workflowId || '');
  const [webhookToken, setWebhookToken] = useState('');
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<WorkflowRun | null>(null);
  const [showRuns, setShowRuns] = useState(false);
  const [validation, setValidation] = useState<{ valid: boolean; errors: string[]; warnings: string[] } | null>(null);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [erroredNodeIds, setErroredNodeIds] = useState<Set<string>>(new Set());
  const [isRunning, setIsRunning] = useState(false);
  const [showWebhookTester, setShowWebhookTester] = useState(false);
  const [webhookPayload, setWebhookPayload] = useState('{\n  "name": "Test Lead",\n  "email": "test@example.com"\n}');
  const [search, setSearch] = useState('');

  const handleSaveRef = useRef<() => Promise<void>>();

  const loadRuns = useCallback(async (id: string) => {
    try {
      const data = await listRuns(id);
      setRuns(data);
      if (data.length > 0) setSelectedRun(data[0]);
    } catch {
      setRuns([]);
    }
  }, []);

  useEffect(() => {
    if (workflowId) {
      getWorkflow(workflowId).then((wf) => {
        setName(wf.name);
        setCurrentId(wf.id);
        setWebhookToken(wf.webhook_token || '');
        setWfStatus(wf.status === 'active' ? 'active' : 'draft');
        const { nodes: n, edges: e } = defToFlow(wf.definition);
        setNodes(n);
        setEdges(e);
        loadRuns(wf.id);
      }).catch(() => setStatus(t('builder.loadFailed')));
    }
  }, [workflowId, setNodes, setEdges, loadRuns]);

  useEffect(() => {
    const runId = searchParams.get('run');
    if (!runId || !currentId) return;
    if (demoRunHandled.current === runId) return;
    demoRunHandled.current = runId;

    setShowRuns(true);
    setIsRunning(true);
    setErroredNodeIds(new Set());
    pollRun(currentId, runId)
      .then(() => loadRuns(currentId))
      .finally(() => setIsRunning(false));
  }, [currentId, searchParams, loadRuns]);

  useEffect(() => {
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: {
          ...n.data,
          running: n.id === activeNodeId,
          errored: erroredNodeIds.has(n.id),
        },
      })),
    );
  }, [activeNodeId, erroredNodeIds, setNodes]);

  const pollRun = async (wfId: string, runId: string) => {
    while (true) {
      const run = await getRun(wfId, runId);
      setSelectedRun(run);
      setRuns((prev) => {
        const idx = prev.findIndex((r) => r.id === runId);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = run;
          return next;
        }
        return [run, ...prev];
      });
      const started = [...(run.logs || [])].reverse().find((l) => l.event === 'started');
      setActiveNodeId(started?.node_id || null);
      const errs = new Set<string>(
        (run.logs || []).filter((l) => l.event === 'error').map((l) => l.node_id),
      );
      setErroredNodeIds(errs);
      if (run.status !== 'running') break;
      await new Promise((r) => setTimeout(r, 500));
    }
    setActiveNodeId(null);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSaveRef.current?.();
      }
      if (e.key === 'Delete' && selectedNode) {
        setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
        setEdges((eds) => eds.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id));
        setSelectedNode(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  const onConnect = useCallback(
    (params: Connection) => {
      const sourceNode = nodes.find((n) => n.id === params.source);
      let label: string | undefined;
      if (params.sourceHandle === 'error') {
        label = 'error';
      } else if (sourceNode && String(sourceNode.data.nodeType) === 'condition') {
        label = window.prompt(t('builder.branchPrompt'), 'true') || 'true';
        if (label !== 'true' && label !== 'false') label = 'true';
      }
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            label,
            animated: true,
            style: edgeStyle(label),
          },
          eds,
        ),
      );
    },
    [setEdges, nodes],
  );

  const addNode = (type: string) => {
    const id = `n${Date.now()}`;
    setNodes((nds) => [
      ...nds,
      {
        id,
        type: 'workflowNode',
        position: { x: 200 + nds.length * 30, y: 150 + nds.length * 20 },
        data: { nodeType: type, nodeId: id, config: {} },
      },
    ]);
  };

  const handleSave = async () => {
    const definition = flowToDef(nodes, edges);
    try {
      if (currentId) {
        await updateWorkflow(currentId, name, definition, wfStatus);
      } else {
        const wf = await createWorkflow(name, definition, wfStatus);
        setCurrentId(wf.id);
        setWebhookToken(wf.webhook_token || '');
        navigate(`/workflows/${wf.id}`, { replace: true });
      }
      setStatus(t('builder.saved'));
      setTimeout(() => setStatus(''), 2000);
    } catch {
      setStatus(t('builder.saveFailed'));
    }
  };
  handleSaveRef.current = handleSave;

  const handleRun = async () => {
    let id = currentId;
    if (!id) {
      const definition = flowToDef(nodes, edges);
      const wf = await createWorkflow(name, definition, wfStatus);
      setCurrentId(wf.id);
      setWebhookToken(wf.webhook_token || '');
      id = wf.id;
      navigate(`/workflows/${wf.id}`, { replace: true });
    }
    setIsRunning(true);
    setShowRuns(true);
    setErroredNodeIds(new Set());
    try {
      const result = await runWorkflow(id, { manual: true }) as { success: boolean; run_id?: string };
      if (result.run_id) {
        await pollRun(id, result.run_id);
      }
      setStatus(result.success ? t('builder.runOk') : t('builder.runFailed'));
      await loadRuns(id);
    } catch {
      setStatus(t('builder.runFailed'));
    } finally {
      setIsRunning(false);
      setActiveNodeId(null);
    }
  };

  const handleValidate = async () => {
    const definition = flowToDef(nodes, edges);
    try {
      const result = await validateWorkflow(definition);
      setValidation(result);
      setStatus(result.valid ? t('builder.valid') : t('builder.validationErrors'));
    } catch {
      setStatus(t('builder.validateFailed'));
    }
  };

  const handleWebhookTest = async () => {
    if (!currentId || !webhookToken) {
      setStatus(t('builder.saveFirstWebhook'));
      return;
    }
    let body: unknown = {};
    try {
      body = JSON.parse(webhookPayload);
    } catch {
      setStatus(t('builder.invalidJson'));
      return;
    }
    try {
      const resp = await fetch(`/api/workflows/webhook/${currentId}?token=${webhookToken}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      setStatus(data?.success ? t('builder.webhookFired') : t('builder.webhookError'));
      if (data?.run_id) {
        await pollRun(currentId, data.run_id);
        await loadRuns(currentId);
      }
    } catch {
      setStatus(t('builder.webhookTestFailed'));
    }
  };

  const updateNodeConfig = (key: string, value: unknown) => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) =>
        n.id === selectedNode.id
          ? { ...n, data: { ...n.data, config: { ...(n.data.config as object), [key]: value } } }
          : n,
      ),
    );
    setSelectedNode((prev) =>
      prev ? { ...prev, data: { ...prev.data, config: { ...(prev.data.config as object), [key]: value } } } : null,
    );
  };

  const updateRetry = (field: 'max_attempts' | 'backoff_seconds', value: number) => {
    if (!selectedNode) return;
    const cfg = (selectedNode.data.config as Record<string, unknown>) || {};
    const retry = { ...((cfg.retry as Record<string, unknown>) || {}), [field]: value };
    updateNodeConfig('retry', retry);
  };

  const filteredCategories = useMemo(() => {
    const term = search.trim().toLowerCase();
    return NODE_CATEGORIES.map((cat) => ({
      ...cat,
      items: NODE_TYPES.filter(
        (nt) =>
          nt.category === cat.id &&
          (!term
            || builderNodeLabel(nt.type).toLowerCase().includes(term)
            || nt.type.toLowerCase().includes(term)),
      ),
    })).filter((cat) => cat.items.length > 0);
  }, [search]);

  const webhookUrl = currentId && webhookToken
    ? `${window.location.origin}/api/workflows/webhook/${currentId}?token=${webhookToken}`
    : '';

  const selectedConfig = (selectedNode?.data.config as Record<string, unknown>) || {};
  const retry = (selectedConfig.retry as Record<string, number>) || {};

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>
      <div style={{ width: 220, borderRight: '1px solid var(--border)', padding: 12, overflowY: 'auto', background: 'var(--bg-secondary)' }}>
        <button className="btn" onClick={() => navigate('/workflows')} style={{ width: '100%', marginBottom: 12 }}>
          {t('builder.back')}
        </button>
        <input
          className="input"
          placeholder={t('builder.searchNodes')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ marginBottom: 12 }}
        />
        {filteredCategories.map((cat) => (
          <div key={cat.id} style={{ marginBottom: 14 }}>
            <h4 style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.6, color: 'var(--text-muted)', marginBottom: 6, paddingLeft: 4 }}>
              {builderCategoryLabel(cat.id)}
            </h4>
            {cat.items.map((nt) => (
              <button
                key={nt.type}
                onClick={() => addNode(nt.type)}
                className="btn"
                style={{
                  width: '100%', marginBottom: 6, textAlign: 'left',
                  borderColor: nt.color, paddingLeft: 8, fontSize: 12,
                }}
                title={nt.type}
              >
                <span style={{
                  display: 'inline-block', width: 22, height: 22, marginRight: 6,
                  background: nt.color, color: '#fff', borderRadius: 4,
                  textAlign: 'center', lineHeight: '22px', fontSize: 9, fontWeight: 700,
                }}>{nt.icon}</span>
                {builderNodeLabel(nt.type)}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', background: 'var(--bg-secondary)' }}>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 200 }} />
          <select className="input" style={{ width: 'auto' }} value={wfStatus} onChange={(e) => setWfStatus(e.target.value as 'draft' | 'active')}>
            <option value="draft">{t('builder.statusDraft')}</option>
            <option value="active">{t('builder.statusActive')}</option>
          </select>
          <button className="btn btn-primary" onClick={handleSave}>{t('builder.save')}</button>
          <button className="btn" onClick={handleRun} disabled={isRunning}>
            {isRunning ? t('builder.running') : t('builder.run')}
          </button>
          <button className="btn" onClick={handleValidate}>{t('builder.validate')}</button>
          <button className="btn" onClick={() => setShowWebhookTester(!showWebhookTester)}>{t('builder.webhook')}</button>
          <button className="btn" onClick={() => setShowRuns(!showRuns)}>{t('builder.runs')} ({runs.length})</button>
          <span style={{ color: 'var(--text-muted)', fontSize: 13, marginLeft: 'auto' }}>{status}</span>
        </div>

        {validation && (
          <div style={{
            padding: '8px 16px',
            background: validation.valid ? '#1f3d2a' : '#3d1f1f',
            fontSize: 12, color: validation.valid ? '#7ee787' : '#ffa198',
            borderBottom: '1px solid var(--border)',
          }}>
            {validation.valid && validation.errors.length === 0 && validation.warnings.length === 0
              ? t('builder.workflowValid')
              : null}
            {validation.errors.map((e, i) => <div key={`e${i}`}>{t('builder.errorPrefix')} {e}</div>)}
            {validation.warnings.map((w, i) => <div key={`w${i}`}>{t('builder.warningPrefix')} {w}</div>)}
          </div>
        )}

        {showWebhookTester && (
          <div style={{ padding: 12, borderBottom: '1px solid var(--border)', background: 'var(--bg-secondary)', fontSize: 12 }}>
            <div style={{ marginBottom: 6, color: 'var(--text-muted)' }}>{t('builder.webhookUrl')}</div>
            <code style={{ display: 'block', padding: 8, background: 'var(--bg)', borderRadius: 4, wordBreak: 'break-all', marginBottom: 8 }}>
              {webhookUrl || t('builder.saveForUrl')}
            </code>
            <textarea
              className="input"
              value={webhookPayload}
              onChange={(e) => setWebhookPayload(e.target.value)}
              style={{ height: 100, fontFamily: 'monospace', fontSize: 12 }}
            />
            <button className="btn btn-primary" onClick={handleWebhookTest} style={{ marginTop: 8 }}>{t('builder.sendTestPayload')}</button>
          </div>
        )}

        <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
          <div style={{ flex: 1 }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={(_, node) => setSelectedNode(node)}
              onPaneClick={() => setSelectedNode(null)}
              nodeTypes={nodeTypes}
              fitView
              defaultEdgeOptions={{ animated: true }}
              style={{ background: 'var(--bg)' }}
            >
              <Background color="#30363d" gap={20} />
              <Controls />
              <MiniMap nodeColor="#238636" maskColor="rgba(0,0,0,0.6)" />
            </ReactFlow>
          </div>

          {showRuns && (
            <div style={{ width: 300, borderLeft: '1px solid var(--border)', padding: 12, overflowY: 'auto', background: 'var(--bg-secondary)' }}>
              <h3 style={{ fontSize: 14, marginBottom: 12 }}>{t('builder.runHistory')}</h3>
              {runs.length === 0 && <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('builder.noRuns')}</p>}
              {runs.map((run) => (
                <div
                  key={run.id}
                  onClick={() => setSelectedRun(run)}
                  style={{
                    padding: 8, marginBottom: 8, borderRadius: 6, cursor: 'pointer',
                    background: selectedRun?.id === run.id ? 'var(--bg-tertiary)' : 'var(--bg)',
                    border: '1px solid var(--border)', fontSize: 12,
                  }}
                >
                  <div>{run.id.slice(0, 16)}...</div>
                  <div style={{ color: run.status === 'success' ? 'var(--success)' : run.status === 'failed' ? '#f85149' : '#d29922' }}>{run.status}</div>
                  <div style={{ color: 'var(--text-muted)' }}>{run.started_at}</div>
                </div>
              ))}
              {selectedRun && (
                <div style={{ marginTop: 16 }}>
                  <h4 style={{ fontSize: 13, marginBottom: 8 }}>{t('builder.timeline')}</h4>
                  <ExecutionTimeline logs={selectedRun.logs || []} activeNodeId={activeNodeId || undefined} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {selectedNode && (
        <div style={{ width: 300, borderLeft: '1px solid var(--border)', padding: 12, overflowY: 'auto', background: 'var(--bg-secondary)' }}>
          <h3 style={{ fontSize: 14 }}>{t('builder.configTitle')}: {String(selectedNode.data.nodeId)}</h3>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>{String(selectedNode.data.nodeType)}</p>

          <NodeConfigEditor
            nodeType={String(selectedNode.data.nodeType)}
            config={selectedConfig}
            onChange={updateNodeConfig}
          />

          <details style={{ marginTop: 14 }}>
            <summary style={{ cursor: 'pointer', fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>
              {t('builder.reliability')}
            </summary>
            <label style={labelStyle}>{t('builder.maxAttempts')}</label>
            <input
              type="number" min={1} max={10}
              className="input"
              value={Number(retry.max_attempts) || 1}
              onChange={(e) => updateRetry('max_attempts', Math.max(1, Math.min(10, Number(e.target.value) || 1)))}
            />
            <label style={labelStyle}>{t('builder.backoffSeconds')}</label>
            <input
              type="number" min={0} step={0.5}
              className="input"
              value={Number(retry.backoff_seconds) || 1}
              onChange={(e) => updateRetry('backoff_seconds', Math.max(0, Number(e.target.value) || 0))}
            />
            <label style={{ ...labelStyle, marginTop: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                type="checkbox"
                checked={Boolean(selectedConfig.continue_on_error)}
                onChange={(e) => updateNodeConfig('continue_on_error', e.target.checked)}
              />
              {t('builder.continueOnError')}
            </label>
          </details>
        </div>
      )}
    </div>
  );
}

interface NodeConfigProps {
  nodeType: string;
  config: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
}

function NodeConfigEditor({ nodeType, config, onChange }: NodeConfigProps) {
  const get = (k: string) => String(config[k] ?? '');
  const f = (key: I18nKey) => t(key);

  if (nodeType.startsWith('agent.')) {
    return (
      <>
        <label style={labelStyle}>{f('builder.fields.prompt')}</label>
        <textarea
          value={get('prompt')}
          onChange={(e) => onChange('prompt', e.target.value)}
          className="input"
          style={{ height: 80 }}
        />
        <label style={labelStyle}>{f('builder.fields.agentId')}</label>
        <input
          value={String(config.agent_id || 'universal')}
          onChange={(e) => onChange('agent_id', e.target.value)}
          className="input"
        />
      </>
    );
  }

  if (nodeType === 'condition') {
    return (
      <>
        <label style={labelStyle}>{f('builder.fields.sourceNode')}</label>
        <input value={get('source_node')} onChange={(e) => onChange('source_node', e.target.value)} className="input" />
        <label style={labelStyle}>{f('builder.fields.field')}</label>
        <input value={String(config.field || 'output')} onChange={(e) => onChange('field', e.target.value)} className="input" />
        <label style={labelStyle}>{f('builder.fields.operator')}</label>
        <select className="input" value={String(config.operator || 'contains')} onChange={(e) => onChange('operator', e.target.value)}>
          <option value="contains">{f('builder.fields.contains')}</option>
          <option value="equals">{f('builder.fields.equals')}</option>
          <option value="not_empty">{f('builder.fields.not_empty')}</option>
          <option value="regex">{f('builder.fields.regex')}</option>
        </select>
        <label style={labelStyle}>{f('builder.fields.value')}</label>
        <input value={get('value')} onChange={(e) => onChange('value', e.target.value)} className="input" />
      </>
    );
  }

  if (nodeType === 'util.set') {
    const valuesJson = JSON.stringify(config.values ?? {}, null, 2);
    return (
      <>
        <label style={labelStyle}>{f('builder.fields.valuesJson')}</label>
        <textarea
          className="input"
          style={{ height: 120, fontFamily: 'monospace', fontSize: 12 }}
          defaultValue={valuesJson}
          onBlur={(e) => {
            try {
              onChange('values', JSON.parse(e.target.value));
            } catch {
              // ignore — keep prior value
            }
          }}
        />
        <label style={labelStyle}>{f('builder.fields.storeKey')}</label>
        <input className="input" value={get('store')} onChange={(e) => onChange('store', e.target.value)} />
      </>
    );
  }

  if (nodeType === 'util.merge') {
    return (
      <>
        <label style={labelStyle}>{f('builder.fields.sources')}</label>
        <input
          className="input"
          value={Array.isArray(config.sources) ? (config.sources as string[]).join(',') : ''}
          onChange={(e) => onChange('sources', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
        />
        <label style={labelStyle}>{f('builder.fields.strategy')}</label>
        <select className="input" value={String(config.strategy || 'shallow')} onChange={(e) => onChange('strategy', e.target.value)}>
          <option value="shallow">{f('builder.fields.shallow')}</option>
          <option value="deep">{f('builder.fields.deep')}</option>
        </select>
      </>
    );
  }

  if (nodeType === 'util.wait') {
    return (
      <>
        <label style={labelStyle}>{f('builder.fields.seconds')}</label>
        <input
          type="number" min={0} max={300}
          className="input"
          value={Number(config.seconds) || 1}
          onChange={(e) => onChange('seconds', Number(e.target.value) || 0)}
        />
      </>
    );
  }

  if (nodeType === 'util.code') {
    return (
      <>
        <label style={labelStyle}>{f('builder.fields.codeScript')}</label>
        <textarea
          className="input"
          style={{ height: 180, fontFamily: 'monospace', fontSize: 12 }}
          value={get('script')}
          onChange={(e) => onChange('script', e.target.value)}
          placeholder={'# Example\noutput = {"score": len(trigger.get("name", ""))}'}
        />
        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
          {f('builder.fields.codeHint')}
        </p>
      </>
    );
  }

  if (nodeType === 'action.http') {
    return (
      <>
        <label style={labelStyle}>{f('builder.fields.url')}</label>
        <input value={get('url')} onChange={(e) => onChange('url', e.target.value)} className="input" />
        <label style={labelStyle}>{f('builder.fields.method')}</label>
        <select className="input" value={String(config.method || 'GET')} onChange={(e) => onChange('method', e.target.value)}>
          {['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
        <label style={labelStyle}>{f('builder.fields.headers')}</label>
        <textarea
          className="input"
          style={{ height: 60, fontFamily: 'monospace', fontSize: 12 }}
          defaultValue={JSON.stringify(config.headers ?? {}, null, 2)}
          onBlur={(e) => {
            try { onChange('headers', JSON.parse(e.target.value)); } catch { /* ignore */ }
          }}
        />
        <label style={labelStyle}>{f('builder.fields.jsonBody')}</label>
        <textarea
          className="input"
          style={{ height: 80, fontFamily: 'monospace', fontSize: 12 }}
          defaultValue={JSON.stringify(config.json ?? {}, null, 2)}
          onBlur={(e) => {
            try { onChange('json', JSON.parse(e.target.value)); } catch { /* ignore */ }
          }}
        />
      </>
    );
  }

  if (nodeType.startsWith('action.')) {
    return (
      <>
        <label style={labelStyle}>{f('builder.fields.messageBody')}</label>
        <textarea
          value={String(config.message || config.body || '')}
          onChange={(e) => onChange(nodeType === 'action.gmail_send' ? 'body' : 'message', e.target.value)}
          className="input"
          style={{ height: 80 }}
        />
        {nodeType === 'action.gmail_send' && (
          <>
            <label style={labelStyle}>{f('builder.fields.to')}</label>
            <input value={get('to')} onChange={(e) => onChange('to', e.target.value)} className="input" />
            <label style={labelStyle}>{f('builder.fields.subject')}</label>
            <input value={get('subject')} onChange={(e) => onChange('subject', e.target.value)} className="input" />
          </>
        )}
        {nodeType === 'action.telegram' && (
          <>
            <label style={labelStyle}>{f('builder.fields.chatId')}</label>
            <input value={get('chat_id')} onChange={(e) => onChange('chat_id', e.target.value)} className="input" />
          </>
        )}
        {nodeType === 'action.slack' && (
          <>
            <label style={labelStyle}>{f('builder.fields.channel')}</label>
            <input value={get('channel')} onChange={(e) => onChange('channel', e.target.value)} className="input" />
          </>
        )}
      </>
    );
  }

  if (nodeType === 'trigger.schedule') {
    return (
      <>
        <label style={labelStyle}>{f('builder.fields.cron')}</label>
        <input value={String(config.cron || '0 9 * * *')} onChange={(e) => onChange('cron', e.target.value)} className="input" />
        <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{f('builder.fields.cronHint')}</p>
      </>
    );
  }

  return <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('builder.noConfig')}</p>;
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 12,
  color: 'var(--text-muted)',
  marginTop: 8,
  marginBottom: 4,
};
