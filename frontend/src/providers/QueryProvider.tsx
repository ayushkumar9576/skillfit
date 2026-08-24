"use client";

/**
 * providers/QueryProvider.tsx
 * ---------------------------
 * Wraps the application with TanStack Query's QueryClientProvider.
 * Must be a Client Component because QueryClient uses browser state.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

interface QueryProviderProps {
  children: ReactNode;
}

export default function QueryProvider({ children }: QueryProviderProps) {
  // useState ensures each browser session gets its own QueryClient instance.
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 5,    // 5 minutes — user data doesn't change often
            retry: 1,                      // 1 retry on failure before reporting error
            refetchOnWindowFocus: false,   // Prevent re-fetching on tab switch
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
