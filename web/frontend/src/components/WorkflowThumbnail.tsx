import { memo } from 'react';
import { NODE_TYPES } from '../types/workflow';

interface NodeLite {
  id: string;
  type: string;
  position?: { x: number; y: number };
}

interface EdgeLite {
  from: string;
  to: string;
  label?: string;
}

interface Props {
  definition?: { nodes?: NodeLite[]; edges?: EdgeLite[] };
  width?: number;
  height?: number;
}

function WorkflowThumbnail({ definition, width = 260, height = 100 }: Props) {
  const nodes = definition?.nodes || [];
  const edges = definition?.edges || [];

  if (nodes.length === 0) {
    return (
      <div
        style={{
          width: '100%', height,
          background: 'var(--bg-tertiary)',
          borderRadius: 6,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-muted)', fontSize: 12,
        }}
      >
        empty workflow
      </div>
    );
  }

  const cols = Math.min(nodes.length, 6);
  const positions: Record<string, { x: number; y: number }> = {};
  nodes.forEach((n, i) => {
    if (n.position) {
      positions[n.id] = n.position;
    } else {
      positions[n.id] = { x: (i % cols) * 60 + 20, y: Math.floor(i / cols) * 50 + 20 };
    }
  });

  const xs = Object.values(positions).map((p) => p.x);
  const ys = Object.values(positions).map((p) => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const spanX = Math.max(maxX - minX, 1);
  const spanY = Math.max(maxY - minY, 1);

  const norm = (p: { x: number; y: number }) => ({
    x: 16 + ((p.x - minX) / spanX) * (width - 32),
    y: 16 + ((p.y - minY) / spanY) * (height - 32),
  });

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
      <defs>
        <marker id="arrow" viewBox="0 -5 10 10" refX="8" refY="0" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,-5L10,0L0,5" fill="#8b949e" />
        </marker>
      </defs>
      {edges.map((e, i) => {
        const src = positions[e.from];
        const dst = positions[e.to];
        if (!src || !dst) return null;
        const a = norm(src);
        const b = norm(dst);
        const labelLower = (e.label || '').toLowerCase();
        const stroke = labelLower === 'false' || labelLower === 'error'
          ? '#f85149'
          : labelLower === 'true'
          ? '#238636'
          : '#58a6ff';
        return (
          <line
            key={`edge-${i}`}
            x1={a.x} y1={a.y} x2={b.x} y2={b.y}
            stroke={stroke} strokeWidth="1.4" markerEnd="url(#arrow)"
            opacity="0.85"
          />
        );
      })}
      {nodes.map((n) => {
        const meta = NODE_TYPES.find((nt) => nt.type === n.type);
        const color = meta?.color || '#30363d';
        const p = norm(positions[n.id]);
        return (
          <g key={n.id} transform={`translate(${p.x - 6},${p.y - 6})`}>
            <rect width="12" height="12" rx="3" fill={color} stroke="#0d1117" strokeWidth="1" />
          </g>
        );
      })}
    </svg>
  );
}

export default memo(WorkflowThumbnail);
