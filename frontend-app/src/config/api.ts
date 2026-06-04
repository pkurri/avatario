const DEFAULT_API_URL = 'http://localhost:8000';

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL?.replace(/\/$/, '') || DEFAULT_API_URL;

export const ELEVENLABS_API_KEY =
  process.env.EXPO_PUBLIC_ELEVENLABS_API_KEY || '';

export function apiUrl(path: string, params?: Record<string, string | number | boolean | undefined>) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = new URL(`${API_BASE_URL}${normalizedPath}`);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
}
