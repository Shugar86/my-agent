import { cloneElement, type ReactElement } from 'react';
import type { FeatureStatus } from './FeatureTag';

interface FeatureGateProps {
  status: FeatureStatus;
  children: ReactElement<{ disabled?: boolean; className?: string; title?: string }>;
  hint?: string;
}

/** Disables child control and marks coming-soon features without silent no-ops. */
export function FeatureGate({ status, children, hint }: FeatureGateProps) {
  if (status !== 'coming-soon') return children;

  const className = [children.props.className, 'feature-gate--soon'].filter(Boolean).join(' ');
  return cloneElement(children, {
    disabled: true,
    className,
    title: hint ?? children.props.title,
  });
}
