import React from "react";
import { Loader2 } from "lucide-react";

export default function DashboardAnalyzingState() {
  return (
    <div className="max-w-4xl mx-auto mt-12 p-8 bg-white border border-slate-200 rounded-xl shadow-sm">
      <div className="flex flex-col items-center justify-center py-10">
        <Loader2 className="h-12 w-12 text-indigo-500 animate-spin mb-6" />
        <h3 className="text-xl font-semibold text-slate-900 mb-2">
          Analysis In Progress
        </h3>
        <p className="text-slate-500 max-w-md text-center">
          The Intelligence Engine is extracting insights and validating evidence. This usually takes 30-60 seconds.
        </p>
        
        {/* Simplified progress representation for Phase 4.7A foundation */}
        <div className="w-full max-w-md mt-8 space-y-4">
          <div className="flex items-center gap-3">
            <div className="h-6 w-6 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-xs font-bold">✓</div>
            <span className="text-sm font-medium text-slate-700">JD Ingestion & Scan</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="h-6 w-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-xs font-bold animate-pulse">2</div>
            <span className="text-sm font-semibold text-slate-900">Intelligence Extraction</span>
          </div>
          <div className="flex items-center gap-3 opacity-50">
            <div className="h-6 w-6 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center text-xs font-bold">3</div>
            <span className="text-sm font-medium text-slate-600">Evidence Governance</span>
          </div>
        </div>
      </div>
    </div>
  );
}
