import React from "react";
import { EvidenceType, IntelligenceOrigin } from "@/types/drives";
import { Sparkles, FileText, CheckCircle2 } from "lucide-react";

interface EvidenceBadgeProps {
  origin?: IntelligenceOrigin;
  evidenceType?: EvidenceType;
  count?: number;
  className?: string;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  ariaExpanded?: boolean;
}

export default function EvidenceBadge({ 
  origin, 
  evidenceType, 
  count, 
  className = "",
  onClick,
  ariaExpanded
}: EvidenceBadgeProps) {
  const isExplicit = origin === IntelligenceOrigin.explicit || 
    evidenceType?.startsWith("EXPLICIT");

  const colors = isExplicit 
    ? "bg-slate-100 text-slate-700 border-slate-200 hover:bg-slate-200" 
    : "bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100";

  const Icon = isExplicit ? FileText : Sparkles;

  return (
    <button 
      onClick={onClick}
      disabled={!onClick}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium border transition-colors ${onClick ? 'cursor-pointer hover:shadow-sm' : 'cursor-default'} ${colors} ${className}`}
      title={isExplicit ? "Explicitly stated in Job Description" : "Inferred by Intelligence Engine"}
      aria-expanded={ariaExpanded}
      aria-haspopup={onClick ? "dialog" : undefined}
    >
      <Icon className="h-3 w-3" />
      {isExplicit ? "Explicit" : "Inferred"}
      {count !== undefined && (
        <span className="ml-1 flex items-center gap-1 opacity-80">
          <span className="w-px h-3 bg-current opacity-30 mx-0.5"></span>
          <CheckCircle2 className="h-3 w-3" />
          {count}
        </span>
      )}
    </button>
  );
}
