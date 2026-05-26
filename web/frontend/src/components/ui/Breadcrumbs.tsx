import { Link } from 'react-router-dom';

export interface BreadcrumbItem {
  label: string;
  to?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

/** Simple breadcrumb trail for nested pages (e.g. Workflows → Builder). */
export default function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav aria-label="breadcrumb" className="breadcrumbs">
      {items.map((item, i) => {
        const isLast = i === items.length - 1;
        return (
          <span key={`${item.label}-${i}`} className="breadcrumbs__segment">
            {i > 0 && <span className="breadcrumbs__sep" aria-hidden>/</span>}
            {item.to && !isLast ? (
              <Link to={item.to} className="breadcrumbs__link">{item.label}</Link>
            ) : (
              <span className="breadcrumbs__current">{item.label}</span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
