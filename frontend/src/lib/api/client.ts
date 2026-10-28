/**
 * lib/api/client.ts
 * -----------------
 * Axios HTTP client instance for the SkillFit frontend.
 *
 * Configuration:
 *  - Base URL read from NEXT_PUBLIC_API_BASE_URL environment variable.
 *    No hardcoded URLs anywhere in source code.
 *  - Request interceptor injects the Bearer token from localStorage.
 *  - Response interceptor clears token on 401 (token expired/invalid).
 */

import axios from "axios";
import { getToken, removeToken } from "@/lib/auth/token";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Inject Bearer token on every outgoing request if one is stored.
apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear the stored token. The AuthProvider will detect the null
// token on its next render cycle and set isAuthenticated = false.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      removeToken();
    }
    return Promise.reject(error);
  }
);

export default apiClient;
