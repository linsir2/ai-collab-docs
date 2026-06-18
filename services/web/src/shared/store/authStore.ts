import { create } from "zustand";
import { apiClient } from "@/shared/api/client";
import type { UserResponse, TokenResponse } from "@/shared/types/contracts";

interface AuthState {
  user: UserResponse | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (displayName: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  login: async (email, password) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const headers: Record<string, string> = {
      "Content-Type": "application/x-www-form-urlencoded",
    };

    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/api/auth/login`, {
      method: "POST",
      headers,
      body: formData.toString(),
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(errorBody.detail || "Login failed");
    }

    const data: TokenResponse = await res.json();

    apiClient.setToken(data.access_token);
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));

    set({ user: data.user, token: data.access_token, isAuthenticated: true });
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

    set({ user: data.user, token: data.access_token, isAuthenticated: true });
  },

  logout: () => {
    apiClient.setToken("");
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    set({ user: null, token: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    const token = localStorage.getItem("token");
    const userStr = localStorage.getItem("user");

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr) as UserResponse;
        apiClient.setToken(token);
        set({ user, token, isAuthenticated: true });
      } catch {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
      }
    }
  },
}));
