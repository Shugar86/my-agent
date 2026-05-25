import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { NODE_TYPES } from '../../types/workflow';

function WorkflowNodeComponent({ data, selected }: NodeProps) {
  const nodeType = NODE_TYPES.find((n) => n.type === data.nodeType);
  const color = nodeType?.color || '#30363d';
  const label = nodeType?.label || String(data.nodeType);
  const icon = nodeType?.icon || '';
  const running = Boolean(data.running);
  const errored = Boolean(data.errored);
  const succeeded = Boolean(data.succeeded);

  const borderColor = running
    ? '#238636'
    : errored
    ? '#f85149'
    : selected
    ? '#58a6ff'
    : color;

  const background = running
    ? 'linear-gradient(135deg, #1f3d2a 0%, #0f1c14 100%)'
    : errored
    ? 'linear-gradient(135deg, #3d1f1f 0%, #1c0f0f 100%)'
    : succeeded
    ? 'linear-gradient(135deg, #161f20 0%, #0d1117 100%)'
    : '#161b22';

  return (
    <div
      style={{
        background,
        border: `2px solid ${borderColor}`,
        borderRadius: 10,
        padding: '10px 14px',
        minWidth: 180,
        color: '#c9d1d9',
        fontSize: 13,
        boxShadow: running
          ? '0 0 16px rgba(35,134,54,0.55)'
          : errored
          ? '0 0 12px rgba(248,81,73,0.45)'
          : selected
          ? '0 0 0 1px rgba(88,166,255,0.4)'
          : '0 1px 3px rgba(0,0,0,0.4)',
        transition: 'box-shadow 0.2s, border-color 0.2s',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: color, width: 10, height: 10 }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 24,
            height: 24,
            borderRadius: 6,
            background: color,
            color: '#fff',
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: 0.5,
          }}
        >
          {icon}
        </span>
        <div>
          <div style={{ fontWeight: 600 }}>{label}</div>
          <div style={{ fontSize: 10, color: '#8b949e' }}>{String(data.nodeId)}</div>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="success"
        style={{ background: color, width: 10, height: 10, left: '35%' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="error"
        style={{ background: '#f85149', width: 10, height: 10, left: '65%' }}
      />
    </div>
  );
}

export default memo(WorkflowNodeComponent);
