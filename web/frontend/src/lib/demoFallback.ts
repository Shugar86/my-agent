export const OFFLINE_SHOWCASE = '/welcome-assets/data/showcase.json';

export interface FetchWithFallbackResult<T> {
  data: T;
  source: 'live' | 'mock';
}

/** Fetch JSON with static fallback when API or network fails. */
export async function fetchWithDemoFallback<T>(
  url: string,
  fallbackUrl: string,
): Promise<FetchWithFallbackResult<T>> {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(String(res.status));
    return { data: (await res.json()) as T, source: 'live' };
  } catch {
    const res = await fetch(fallbackUrl);
    if (!res.ok) throw new Error('Fallback unavailable');
    return { data: (await res.json()) as T, source: 'mock' };
  }
}
