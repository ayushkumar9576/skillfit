"use client";

/**
 * hooks/useAuth.ts
 * ----------------
 * Convenience hook that re-exports the auth context for cleaner component usage.
 * Import this hook in components instead of importing useAuthContext directly.
 */

import { useAuthContext } from "@/providers/AuthProvider";

export function useAuth() {
  return useAuthContext();
}
