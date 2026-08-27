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
import type { AuthState, User, LoginRequest } from "@/types/auth";

const AuthContext = createContext<AuthState | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export default function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /** Attempt to restore session from a stored token. */
  const restoreSession = useCallback(async () => {
    const currentToken = getToken();
    if (!currentToken) {
      setIsLoading(false);
      return;
    }
    setTokenState(currentToken);
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      // Token is expired, invalid, or server is unreachable — clear it.
      removeToken();
      setTokenState(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Restore session on initial mount.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    restoreSession();
  }, [restoreSession]);

  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      const { access_token } = await import("@/lib/api/auth").then(m => m.loginUser(credentials));
      setToken(access_token);
      setTokenState(access_token);
      
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      removeToken();
      setTokenState(null);
      setUser(null);
      throw err;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      // Ignore or handle
    }
  }, []);

  /**
   * Clear auth state and redirect to home.
   */
  const logout = useCallback(() => {
    removeToken();
    setTokenState(null);
    setUser(null);
    router.push("/");
  }, [router]);

  const value: AuthState = {
    user,
    token,
    isAuthenticated: user !== null,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/** Hook to access the authentication context. Must be used inside AuthProvider. */
export function useAuthContext(): AuthState {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
}
