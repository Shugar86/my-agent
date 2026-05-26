import offlineShowcase from '../../../../website/data/showcase.json';

export const OFFLINE_SHOWCASE_URL = '/welcome-assets/data/showcase.json';

export interface FetchWithFallbackResult<T> {
  data: T;
  source: 'live' | 'mock';
}

/** Fetch JSON; on failure use bundled showcase snapshot (marks source as mock). */
export async function fetchWithDemoFallback<T>(
  url: string = OFFLINE_SHOWCASE_URL,
): Promise<FetchWithFallbackResult<T>> {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(String(res.status));
    return { data: (await res.json()) as T, source: 'live' };
  } catch {
    return { data: offlineShowcase as T, source: 'mock' };
  }
}
