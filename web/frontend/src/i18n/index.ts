import ru from './ru';
import en from './en';

type NestedKeys<T, Prefix extends string = ''> = T extends object
  ? {
      [K in keyof T & string]: T[K] extends object
        ? NestedKeys<T[K], `${Prefix}${K}.`>
        : `${Prefix}${K}`;
    }[keyof T & string]
  : never;

export type I18nKey = NestedKeys<typeof ru>;

function getLocale(): 'ru' | 'en' {
  if (typeof window === 'undefined') return 'ru';
  return localStorage.getItem('my-agent.locale') === 'en' ? 'en' : 'ru';
}

function activeMessages(): Record<string, unknown> {
  if (getLocale() === 'en') {
    return {
      ...ru,
      landing: { ...ru.landing, ...en.landing },
      narrative: { ...ru.narrative, ...en.narrative },
    } as Record<string, unknown>;
  }
  return ru as unknown as Record<string, unknown>;
}

function getNested(obj: Record<string, unknown>, path: string): string {
  const parts = path.split('.');
  let cur: unknown = obj;
  for (const p of parts) {
    if (cur == null || typeof cur !== 'object') return path;
    cur = (cur as Record<string, unknown>)[p];
  }
  return typeof cur === 'string' ? cur : path;
}

function interpolate(template: string, params?: Record<string, string | number>): string {
  if (!params) return template;
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) =>
    params[key] != null ? String(params[key]) : `{{${key}}}`,
  );
}

/** Returns a localized string by dot-path key. */
export function t(key: I18nKey, params?: Record<string, string | number>): string {
  return interpolate(getNested(activeMessages(), key), params);
}

export { ru, en };
