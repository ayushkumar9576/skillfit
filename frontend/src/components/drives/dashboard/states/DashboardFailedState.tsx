import React from "react";
import { AlertOctagon, RefreshCw } from "lucide-react";

interface DashboardFailedStateProps {
  errorMessage?: string | null;
  onRetry: () => void;
  isRetrying?: boolean;
}

export default function DashboardFailedState({ errorMessage, onRetry, isRetrying }: DashboardFailedStateProps) {
  return (
    <div className="max-w-3xl mx-auto mt-12 p-8 bg-rose-50 border border-rose-200 rounded-xl shadow-sm">
      <div className="flex flex-col items-center text-center">
        <div className="h-14 w-14 bg-rose-100 rounded-full flex items-center justify-center mb-5">
          <AlertOctagon className="h-7 w-7 text-rose-600" />
        </div>
        <h3 className="text-xl font-bold text-rose-900 mb-2">
          Analysis Pipeline Failed
        </h3>
        <p className="text-rose-700 max-w-lg mb-6">
          The Intelligence Engine or Governance Layer encountered an unrecoverable error during processing.
        </p>
        
        {errorMessage && (
          <div className="w-full bg-white bg-opacity-60 rounded-lg p-4 mb-8 text-left border border-rose-100 overflow-auto">
            <p className="text-sm font-mono text-rose-800 break-words">
              {errorMessage}
            </p>
          </div>
        )}

        <button
          onClick={onRetry}
          disabled={isRetrying}
          className="flex items-center gap-2 px-6 py-2.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed shadow-sm"
        >
          <RefreshCw className={`h-4 w-4 ${isRetrying ? 'animate-spin' : ''}`} />
          {isRetrying ? "Retrying..." : "Re-run Analysis"}
        </button>
      </div>
    </div>
  );
}
