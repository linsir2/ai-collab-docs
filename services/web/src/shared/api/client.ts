const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

let _token: string | null = null;

export const apiClient = {
  setToken(token: string) {
    _token = token;
  },

  getToken(): string | null {
    return _token;
  },

  async request<T = unknown>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (_token) {
      headers["Authorization"] = `Bearer ${_token}`;
    }

    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errorBody.detail || `Request failed: ${res.status}`);
    }

    if (res.status === 204) {
      return undefined as T;
    }

    return res.json() as Promise<T>;
  },

  get<T = unknown>(path: string): Promise<T> {
    return this.request<T>("GET", path);
  },

  post<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("POST", path, body);
  },

  put<T = unknown>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("PUT", path, body);
  },

  del<T = unknown>(path: string): Promise<T> {
    return this.request<T>("DELETE", path);
  },
};

export function wsClient(docId: string, token: string): WebSocket {
  const ws = new WebSocket(`${WS_URL}/api/collab/ws/${docId}?token=${token}`);

  return ws;
}
