import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { NODE_TYPES } from '../../types/workflow';

function WorkflowNodeComponent({ data, selected }: NodeProps) {
  const nodeType = NODE_TYPES.find((n) => n.type === data.nodeType);
  const color = nodeType?.color || '#30363d';
  const label = nodeType?.label || String(data.nodeType);
  const running = Boolean(data.running);

  return (
    <div
      style={{
        background: running ? '#1f3d2a' : '#161b22',
        border: `2px solid ${running ? '#238636' : selected ? '#58a6ff' : color}`,
        borderRadius: 8,
        padding: '10px 16px',
        minWidth: 160,
        color: '#c9d1d9',
        fontSize: 13,
        boxShadow: running ? '0 0 12px rgba(35,134,54,0.5)' : undefined,
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: color }} />
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 11, color: '#8b949e' }}>{String(data.nodeId)}</div>
      <Handle type="source" position={Position.Bottom} style={{ background: color }} />
    </div>
  );
}

export default memo(WorkflowNodeComponent);
