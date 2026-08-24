"use client";

/**
 * providers/AuthProvider.tsx
 * --------------------------
 * Global authentication state manager for the SkillFit frontend.
 *
 * Responsibilities:
 *  - On mount: reads token from localStorage, calls GET /auth/me to restore session.
 *  - login(token): stores the token then fetches the user identity.
 *  - logout(): clears the token and user state, redirects to home.
 *  - Exposes: user, isAuthenticated, isLoading via AuthContext.
 *
 * Error handling:
 *  - If GET /auth/me fails (expired token, server down): clears token, sets user = null.
 *    The application never crashes — always transitions to a defined state.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser } from "@/lib/api/auth";
import { getToken, removeToken, setToken } from "@/lib/auth/token";
import type { AuthContextValue, User } from "@/types/auth";

const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export default function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /** Attempt to restore session from a stored token. */
  const restoreSession = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      // Token is expired, invalid, or server is unreachable — clear it.
      removeToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Restore session on initial mount.
  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  /**
   * Store the access token and fetch the user identity.
   * Called by LoginForm after a successful POST /auth/login.
   */
  const login = useCallback(async (token: string) => {
    setToken(token);
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      // If /auth/me fails immediately after login, clear state cleanly.
      removeToken();
      setUser(null);
      throw new Error("Failed to load user profile after login.");
    }
  }, []);

  /**
   * Clear auth state and redirect to home.
   */
  const logout = useCallback(() => {
    removeToken();
    setUser(null);
    router.push("/");
  }, [router]);

  const value: AuthContextValue = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Hook to access the authentication context. Must be used inside AuthProvider. */
export function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
}
