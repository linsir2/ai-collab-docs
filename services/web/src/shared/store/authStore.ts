import { create } from "zustand";
import { apiClient } from "@/shared/api/client";
import { GlobalRole, UserRole } from "@/shared/types/contracts";
import type { UserResponse, TokenResponse } from "@/shared/types/contracts";
import { ViewType, canAccessView } from "@/shared/authz";

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  globalRole: GlobalRole | null;
  docRole: UserRole | null;
  currentView: ViewType;
  opsConfirmed: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (displayName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  loadFromStorage: () => void;
  setDocRole: (docId: string) => Promise<void>;
  clearDocRole: () => void;
  setView: (view: ViewType) => void;
  confirmOps: () => void;
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const payload = token.split(".")[1]?.replace(/-/g, "+").replace(/_/g, "/");
    if (!payload) return null;
    return JSON.parse(atob(payload)) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function parseGlobalRole(value: unknown): GlobalRole {
  if (typeof value === "string" && Object.values(GlobalRole).includes(value as GlobalRole)) {
    return value as GlobalRole;
  }
  return GlobalRole.PERSONAL;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  globalRole: null,
  docRole: null,
  currentView: ViewType.FORGE,
  opsConfirmed: false,
  isAuthenticated: false,

  login: async (email, password) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const headers: Record<string, string> = {
      "Content-Type": "application/x-www-form-urlencoded",
    };

    const res = await fetch(
      `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/api/auth/login`,
      {
        method: "POST",
        headers,
        body: formData.toString(),
      }
    );

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(errorBody.detail || "Login failed");
    }

    const data: TokenResponse = await res.json();

    apiClient.setToken(data.access_token);
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));

    set({
      user: data.user,
      token: data.access_token,
      globalRole: parseGlobalRole(data.user.global_role),
      docRole: null,
      isAuthenticated: true,
    });
  },

  register: async (displayName, email, password) => {
    const data = await apiClient.post<TokenResponse>("/api/auth/register", {
      display_name: displayName,
      email,
      password,
    });

    apiClient.setToken(data.access_token);
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));

    set({
      user: data.user,
      token: data.access_token,
      globalRole: parseGlobalRole(data.user.global_role),
      docRole: null,
      isAuthenticated: true,
    });
  },

  logout: () => {
    apiClient.setToken("");
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    set({
      user: null,
      token: null,
      globalRole: null,
      docRole: null,
      isAuthenticated: false,
    });
  },

  loadFromStorage: () => {
    const token = localStorage.getItem("token");
    const userStr = localStorage.getItem("user");

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as UserResponse;
        apiClient.setToken(token);

        const payload = decodeJwtPayload(token);
        const globalRole = parseGlobalRole(user.global_role ?? payload?.global_role);

        set({
          user,
          token,
          globalRole,
          docRole: null,
          isAuthenticated: true,
        });
      } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
      }
    }
  },

  setDocRole: async (docId) => {
    const data = await apiClient.get<UserResponse>(
      `/api/auth/me?doc_id=${encodeURIComponent(docId)}`
    );
    set({
      docRole: data.doc_role ? (data.doc_role as UserRole) : null,
    });
  },

  clearDocRole: () => set({ docRole: null }),

  setView: (view) => {
    const role = get().globalRole;
    if (!role || !canAccessView(role, view)) return;
    set({ currentView: view });
  },

  confirmOps: () => set({ opsConfirmed: true }),
}));
