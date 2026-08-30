"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, FileText, CheckCircle2 } from "lucide-react";
import type { IntelligenceEvidence } from "@/types/candidate-profile";
import EvidenceSourceBadge from "@/components/shared/EvidenceSourceBadge";
import DemonstrationLevelBadge from "@/components/shared/DemonstrationLevelBadge";

interface EvidenceExplorerProps {
  title: string;
  evidence: IntelligenceEvidence[];
  level?: string; // DemonstrationLevel or VerificationStatus
}

export default function EvidenceExplorer({ title, evidence, level }: EvidenceExplorerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm transition-all">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between bg-slate-50 p-4 text-left hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-inset"
      >
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-slate-900">{title}</span>
            {level && (
              <DemonstrationLevelBadge level={level} />
            )}
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-500 mt-1">
            <span>{evidence.length} Evidence Found</span>
          </div>
        </div>
        <div className="flex shrink-0 items-center justify-center h-8 w-8 rounded-full bg-white shadow-sm border border-slate-200 text-slate-500">
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>
      
      {isExpanded && (
        <div className="border-t border-slate-200 bg-white p-4">
          <h4 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-900">
            <FileText className="h-4 w-4 text-indigo-500" />
            Detected Evidence
          </h4>
          
          {evidence.length === 0 ? (
            <p className="text-sm text-slate-500 italic">No direct evidence extracted.</p>
          ) : (
            <ul className="space-y-4">
              {evidence.map((ev, index) => (
                <li key={index} className="flex gap-3 text-sm pb-4 border-b border-slate-100 last:border-0 last:pb-0">
                  <div className="mt-0.5 shrink-0">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  </div>
                  <div className="flex flex-col gap-2">
                    <p className="text-slate-700 italic max-w-4xl leading-relaxed">
                      &ldquo;{ev.quote}&rdquo;
                    </p>
                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      <EvidenceSourceBadge source={ev.source} />
                      {ev.source_id && (
                        <span className="text-xs font-medium text-slate-700">
                          {ev.source_id}
                        </span>
                      )}
                      <span className="text-xs text-slate-400">•</span>
                      {ev.section && (
                        <span className="text-xs text-slate-500 capitalize">
                          Section: {ev.section}
                        </span>
                      )}
                      {ev.line_reference && (
                        <span className="text-xs text-slate-500">
                          (Line {ev.line_reference})
                        </span>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
