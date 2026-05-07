export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL?.replace(/\/$/, "") ||
  API_BASE.replace(/^http/, "ws");

export function apiUrl(path: string) {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export function wsUrl(path: string) {
  return `${WS_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}
