import React from "react";
import { FileSearch, Sparkles } from "lucide-react";

interface DashboardEmptyStateProps {
  onRunAnalysis: () => void;
  isTriggering?: boolean;
}

export default function DashboardEmptyState({ onRunAnalysis, isTriggering }: DashboardEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 mt-8 text-center border-2 border-dashed border-slate-200 rounded-xl bg-white max-w-3xl mx-auto shadow-sm">
      <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mb-6">
        <FileSearch className="h-8 w-8 text-slate-500" />
      </div>
      <h3 className="text-xl font-semibold text-slate-900 mb-2">
        Intelligence Profile Not Generated
      </h3>
      <p className="text-slate-500 max-w-md mx-auto mb-8">
        This drive has ingested job description sources, but has not completed intelligence extraction.
      </p>
      <button
        onClick={onRunAnalysis}
        disabled={isTriggering}
        className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed shadow-sm"
      >
        <Sparkles className="h-5 w-5" />
        {isTriggering ? "Triggering..." : "Run Intelligence Engine"}
      </button>
    </div>
  );
}
