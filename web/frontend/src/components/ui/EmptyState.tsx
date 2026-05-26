import { Link } from 'react-router-dom';

interface EmptyStateProps {
  title: string;
  description?: string;
  actionLabel?: string;
  actionTo?: string;
  onAction?: () => void;
  secondaryActionLabel?: string;
  secondaryOnAction?: () => void;
}

/** Centered empty state with optional CTA link or button. */
export default function EmptyState({
  title,
  description,
  actionLabel,
  actionTo,
  onAction,
  secondaryActionLabel,
  secondaryOnAction,
}: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon" aria-hidden>◇</div>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
        {actionLabel && actionTo && (
          <Link to={actionTo} className="btn btn-primary">{actionLabel}</Link>
        )}
        {actionLabel && onAction && !actionTo && (
          <button type="button" className="btn btn-primary" onClick={onAction}>{actionLabel}</button>
        )}
        {secondaryActionLabel && secondaryOnAction && (
          <button type="button" className="btn" onClick={secondaryOnAction}>{secondaryActionLabel}</button>
        )}
      </div>
    </div>
  );
}
