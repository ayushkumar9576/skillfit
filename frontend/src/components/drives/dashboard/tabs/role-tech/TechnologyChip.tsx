import React, { memo } from "react";
import { ImportanceLevel, TechnologyIntelligence } from "@/types/drives";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { AlertCircle } from "lucide-react";

interface TechnologyChipProps {
  technology: TechnologyIntelligence;
}

const TechnologyChip = memo(function TechnologyChip({ technology }: TechnologyChipProps) {
  const isMandatory = technology.is_mandatory;
  const isCritical = technology.importance === ImportanceLevel.critical;

  // Determine base styles based on mandatory vs preferred
  const baseClasses = isMandatory
    ? "bg-indigo-50 border-indigo-200 text-indigo-900"
    : "bg-slate-50 border-slate-200 text-slate-700";

  return (
    <div className={`flex flex-col border rounded-lg overflow-hidden min-w-[140px] max-w-sm ${baseClasses}`}>
      <div className="flex items-center justify-between p-2 pb-1 gap-4">
        <span className="font-semibold text-sm leading-tight flex items-center gap-1.5">
          {isCritical && <AlertCircle className="h-3.5 w-3.5 text-rose-500" />}
          {technology.name}
        </span>
        <EvidenceTrigger evidence={technology.evidence} title={`Evidence for ${technology.name}`} />
      </div>
      
      <div className="flex items-center gap-2 p-2 pt-1 mt-auto">
        <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
          isMandatory ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-200 text-slate-600'
        }`}>
          {isMandatory ? 'Mandatory' : 'Preferred'}
        </span>
        
        <span className={`text-[10px] font-bold uppercase tracking-wider ${
          isCritical ? 'text-rose-600' :
          technology.importance === ImportanceLevel.high ? 'text-orange-600' :
          'text-slate-500'
        }`}>
          {technology.importance}
        </span>
      </div>
    </div>
  );
});

export default TechnologyChip;
