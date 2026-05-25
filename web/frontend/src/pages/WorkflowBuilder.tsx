import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
import { NODE_TYPES, type WorkflowDefinition } from '../types/workflow';
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

const nodeTypes = { workflowNode: WorkflowNodeComponent };

function defToFlow(definition: WorkflowDefinition): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = definition.nodes.map((n, i) => ({
    id: n.id,
    type: 'workflowNode',
    position: n.position || { x: 100 + (i % 3) * 220, y: 80 + Math.floor(i / 3) * 120 },
    data: { nodeType: n.type, nodeId: n.id, config: n.config },
  }));
  const edges: Edge[] = definition.edges.map((e, i) => ({
    id: `e${i}`,
    source: e.from,
    target: e.to,
    label: e.label,
    animated: true,
    style: { stroke: e.label === 'false' ? '#f85149' : e.label === 'true' ? '#238636' : '#58a6ff' },
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
  const workflowId = paramId === 'new' ? undefined : paramId;

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [name, setName] = useState('New Workflow');
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [status, setStatus] = useState('');
  const [wfStatus, setWfStatus] = useState<'draft' | 'active'>('draft');
  const [currentId, setCurrentId] = useState(workflowId || '');
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<WorkflowRun | null>(null);
  const [showRuns, setShowRuns] = useState(false);
  const [validation, setValidation] = useState<{ valid: boolean; errors: string[]; warnings: string[] } | null>(null);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

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
        setWfStatus(wf.status === 'active' ? 'active' : 'draft');
        const { nodes: n, edges: e } = defToFlow(wf.definition);
        setNodes(n);
        setEdges(e);
        loadRuns(wf.id);
      }).catch(() => setStatus('Failed to load workflow'));
    }
  }, [workflowId, setNodes, setEdges, loadRuns]);

  useEffect(() => {
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        data: { ...n.data, running: n.id === activeNodeId },
      })),
    );
  }, [activeNodeId, setNodes]);

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
      if (run.status !== 'running') break;
      await new Promise((r) => setTimeout(r, 500));
    }
    setActiveNodeId(null);
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
      if (e.key === 'Delete' && selectedNode) {
        setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
        setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
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
      if (sourceNode && String(sourceNode.data.nodeType) === 'condition') {
        label = window.prompt('Branch label (true/false):', 'true') || 'true';
        if (label !== 'true' && label !== 'false') label = 'true';
      }
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            label,
            animated: true,
            style: { stroke: label === 'false' ? '#f85149' : label === 'true' ? '#238636' : '#58a6ff' },
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
        navigate(`/workflows/${wf.id}`, { replace: true });
      }
      setStatus('Saved!');
      setTimeout(() => setStatus(''), 2000);
    } catch {
      setStatus('Save failed');
    }
  };

  const handleRun = async () => {
    let id = currentId;
    if (!id) {
      const definition = flowToDef(nodes, edges);
      const wf = await createWorkflow(name, definition, wfStatus);
      setCurrentId(wf.id);
      id = wf.id;
      navigate(`/workflows/${wf.id}`, { replace: true });
    }
    setIsRunning(true);
    setShowRuns(true);
    try {
      const result = await runWorkflow(id, { manual: true }) as { success: boolean; run_id?: string };
      if (result.run_id) {
        await pollRun(id, result.run_id);
      }
      setStatus(`Run ${result.success ? 'OK' : 'failed'}`);
      await loadRuns(id);
    } catch {
      setStatus('Run failed');
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
      setStatus(result.valid ? 'Valid ✓' : 'Validation errors');
    } catch {
      setStatus('Validate failed');
    }
  };

  const updateNodeConfig = (key: string, value: string) => {
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

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 0px)', background: 'var(--bg)', color: 'var(--text)' }}>
      <div style={{ width: 200, borderRight: '1px solid var(--border)', padding: 12, overflowY: 'auto' }}>
        <button className="btn" onClick={() => navigate('/workflows')} style={{ width: '100%', marginBottom: 12 }}>← Back</button>
        <h3 style={{ fontSize: 14, margin: '12px 0 8px', color: 'var(--text-muted)' }}>Nodes</h3>
        {NODE_TYPES.map((nt) => (
          <button key={nt.type} onClick={() => addNode(nt.type)} className="btn" style={{ width: '100%', marginBottom: 6, textAlign: 'left', borderColor: nt.color }}>
            {nt.label}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <input className="input" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 180 }} />
          <select className="input" style={{ width: 'auto' }} value={wfStatus} onChange={(e) => setWfStatus(e.target.value as 'draft' | 'active')}>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
          </select>
          <button className="btn btn-primary" onClick={handleSave}>Save</button>
          <button className="btn" onClick={handleRun} disabled={isRunning}>Run</button>
          <button className="btn" onClick={handleValidate}>Validate</button>
          <button className="btn" onClick={() => setShowRuns(!showRuns)}>Runs ({runs.length})</button>
          <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>{status}</span>
        </div>

        {validation && !validation.valid && (
          <div style={{ padding: '8px 16px', background: '#3d1f1f', fontSize: 12 }}>
            {validation.errors.map((e, i) => <div key={i}>⚠ {e}</div>)}
          </div>
        )}

        <div style={{ flex: 1, display: 'flex' }}>
          <div style={{ flex: 1 }}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={(_, node) => setSelectedNode(node)}
              nodeTypes={nodeTypes}
              fitView
              style={{ background: 'var(--bg)' }}
            >
              <Background color="#30363d" gap={20} />
              <Controls />
              <MiniMap nodeColor="#238636" maskColor="rgba(0,0,0,0.6)" />
            </ReactFlow>
          </div>

          {showRuns && (
            <div style={{ width: 280, borderLeft: '1px solid var(--border)', padding: 12, overflowY: 'auto' }}>
              <h3 style={{ fontSize: 14, marginBottom: 12 }}>Run History</h3>
              {runs.map((run) => (
                <div
                  key={run.id}
                  onClick={() => setSelectedRun(run)}
                  style={{
                    padding: 8, marginBottom: 8, borderRadius: 6, cursor: 'pointer',
                    background: selectedRun?.id === run.id ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
                    border: '1px solid var(--border)', fontSize: 12,
                  }}
                >
                  <div>{run.id.slice(0, 16)}...</div>
                  <div style={{ color: run.status === 'success' ? 'var(--success)' : '#f85149' }}>{run.status}</div>
                  <div style={{ color: 'var(--text-muted)' }}>{run.started_at}</div>
                </div>
              ))}
              {selectedRun && (
                <div style={{ marginTop: 16 }}>
                  <h4 style={{ fontSize: 13, marginBottom: 8 }}>Timeline</h4>
                  <ExecutionTimeline logs={selectedRun.logs || []} activeNodeId={activeNodeId || undefined} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {selectedNode && (
        <div style={{ width: 260, borderLeft: '1px solid var(--border)', padding: 12, overflowY: 'auto' }}>
          <h3 style={{ fontSize: 14 }}>Config: {String(selectedNode.data.nodeId)}</h3>
          <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>{String(selectedNode.data.nodeType)}</p>
          {String(selectedNode.data.nodeType).startsWith('agent.') && (
            <>
              <label style={labelStyle}>Prompt</label>
              <textarea
                value={String((selectedNode.data.config as Record<string, string>)?.prompt || '')}
                onChange={(e) => updateNodeConfig('prompt', e.target.value)}
                className="input"
                style={{ height: 80 }}
              />
              <label style={labelStyle}>Agent ID</label>
              <input
                value={String((selectedNode.data.config as Record<string, string>)?.agent_id || 'universal')}
                onChange={(e) => updateNodeConfig('agent_id', e.target.value)}
                className="input"
              />
            </>
          )}
          {String(selectedNode.data.nodeType) === 'condition' && (
            <>
              <label style={labelStyle}>Source Node</label>
              <input
                value={String((selectedNode.data.config as Record<string, string>)?.source_node || '')}
                onChange={(e) => updateNodeConfig('source_node', e.target.value)}
                className="input"
              />
              <label style={labelStyle}>Field</label>
              <input
                value={String((selectedNode.data.config as Record<string, string>)?.field || 'output')}
                onChange={(e) => updateNodeConfig('field', e.target.value)}
                className="input"
              />
              <label style={labelStyle}>Operator</label>
              <select
                className="input"
                value={String((selectedNode.data.config as Record<string, string>)?.operator || 'contains')}
                onChange={(e) => updateNodeConfig('operator', e.target.value)}
              >
                <option value="contains">contains</option>
                <option value="equals">equals</option>
                <option value="not_empty">not_empty</option>
              </select>
              <label style={labelStyle}>Value</label>
              <input
                value={String((selectedNode.data.config as Record<string, string>)?.value || '')}
                onChange={(e) => updateNodeConfig('value', e.target.value)}
                className="input"
              />
            </>
          )}
          {String(selectedNode.data.nodeType).startsWith('action.') && (
            <>
              <label style={labelStyle}>Message / Body</label>
              <textarea
                value={String((selectedNode.data.config as Record<string, string>)?.message || (selectedNode.data.config as Record<string, string>)?.body || '')}
                onChange={(e) => updateNodeConfig('message', e.target.value)}
                className="input"
                style={{ height: 80 }}
              />
            </>
          )}
          {String(selectedNode.data.nodeType) === 'trigger.schedule' && (
            <>
              <label style={labelStyle}>Cron (5 fields)</label>
              <input
                value={String((selectedNode.data.config as Record<string, string>)?.cron || '0 9 * * *')}
                onChange={(e) => updateNodeConfig('cron', e.target.value)}
                className="input"
              />
            </>
          )}
        </div>
      )}
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: 12,
  color: 'var(--text-muted)',
  marginTop: 8,
  marginBottom: 4,
};
