/**
 * lib/auth/token.ts
 * -----------------
 * JWT token helpers for localStorage-based token persistence.
 * All access to the token should go through these helpers — never
 * directly access localStorage in components or hooks.
 */

const TOKEN_KEY = "skillfit_access_token";

/** Retrieve the stored JWT access token, or null if none exists. */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/** Persist a JWT access token to localStorage. */
export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

/** Remove the JWT access token from localStorage (logout). */
export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}
