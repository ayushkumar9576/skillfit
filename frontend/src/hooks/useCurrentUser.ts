"use client";

/**
 * hooks/useCurrentUser.ts
 * -----------------------
 * TanStack Query hook for fetching the authenticated user's profile.
 * Calls GET /auth/me and returns the result with loading and error states.
 */

import { useQuery } from "@tanstack/react-query";
import { getCurrentUser } from "@/lib/api/auth";
import { useAuth } from "@/hooks/useAuth";
import type { User } from "@/types/auth";

export const CURRENT_USER_QUERY_KEY = ["currentUser"] as const;

export function useCurrentUser() {
  const { isAuthenticated } = useAuth();

  return useQuery<User, Error>({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: getCurrentUser,
    enabled: isAuthenticated, // Only fetch when a token exists
  });
}
