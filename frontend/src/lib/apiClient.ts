import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "../features/auth/authStore";
import type { AuthResponse } from "../types/auth";

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

const refreshClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ detail?: string }>) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;
    const refreshToken = useAuthStore.getState().refreshToken;

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && refreshToken) {
      originalRequest._retry = true;

      try {
        const response = await refreshClient.post<AuthResponse>("/auth/refresh", {
          refresh_token: refreshToken,
        });
        useAuthStore
          .getState()
          .setSession(response.data.user, response.data.tokens.access_token, response.data.tokens.refresh_token);
        originalRequest.headers.Authorization = `Bearer ${response.data.tokens.access_token}`;
        return apiClient(originalRequest);
      } catch {
        useAuthStore.getState().logout();
      }
    }

    const message =
      error.response?.data?.detail ??
      error.message ??
      "Something went wrong. Please try again.";
    return Promise.reject(new Error(message));
  },
);
