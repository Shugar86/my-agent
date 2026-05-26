import { useEffect, useState } from 'react';
import { fetchWithDemoFallback } from '../lib/demoFallback';

interface DemoAwareResult<T> {
  data: T | null;
  source: 'live' | 'mock';
  loading: boolean;
  error: string | null;
}

/** Fetch with bundled JSON fallback; exposes live vs preview source. */
export function useDemoAwareFetch<T>(url: string): DemoAwareResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [source, setSource] = useState<'live' | 'mock'>('live');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchWithDemoFallback<T>(url)
      .then(({ data: fetched, source: src }) => {
        if (cancelled) return;
        setData(fetched);
        setSource(src);
      })
      .catch(() => {
        if (cancelled) return;
        setSource('mock');
        setError('fallback');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [url]);

  return { data, source, loading, error };
}
