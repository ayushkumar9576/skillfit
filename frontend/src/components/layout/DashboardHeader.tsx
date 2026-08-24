"use client";

/**
 * components/layout/DashboardHeader.tsx
 * ----------------------------------------
 * Top header bar for the protected dashboard shell.
 */

import { useAuth } from "@/hooks/useAuth";
import { RefreshCw } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { CURRENT_USER_QUERY_KEY } from "@/hooks/useCurrentUser";

export default function DashboardHeader() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
  };

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-100 bg-white px-6">
      {/* Page title area */}
      <div>
        <h1 className="text-sm font-semibold text-slate-900">Dashboard</h1>
        <p className="text-xs text-slate-400">
          Overview of your placement intelligence
        </p>
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-3">
        {/* Refresh button */}
        <button
          type="button"
          onClick={handleRefresh}
          title="Refresh profile data"
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />
          Refresh
        </button>

        {/* User avatar */}
        {user && (
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold uppercase text-indigo-700"
            title={user.full_name}
            aria-label={`Logged in as ${user.full_name}`}
          >
            {user.full_name.slice(0, 2)}
          </div>
        )}
      </div>
    </header>
  );
}
