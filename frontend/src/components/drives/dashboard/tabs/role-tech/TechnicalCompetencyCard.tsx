import React from "react";
import { ImportanceLevel, TechnicalCompetencyIntelligence } from "@/types/drives";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { ShieldCheck, Cpu } from "lucide-react";

interface TechnicalCompetencyCardProps {
  competency: TechnicalCompetencyIntelligence;
}

export default function TechnicalCompetencyCard({ competency }: TechnicalCompetencyCardProps) {
  const isCritical = competency.importance === ImportanceLevel.critical;
  const isHigh = competency.importance === ImportanceLevel.high;

  return (
    <div className={`flex flex-col p-4 border rounded-xl shadow-sm transition-shadow hover:shadow-md ${
      isCritical ? "border-rose-200 bg-rose-50/30" : 
      isHigh ? "border-indigo-200 bg-indigo-50/30" : 
      "border-slate-200 bg-white"
    }`}>
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2.5">
          <div className={`p-1.5 rounded-lg ${
            isCritical ? "bg-rose-100 text-rose-600" :
            isHigh ? "bg-indigo-100 text-indigo-600" :
            "bg-slate-100 text-slate-600"
          }`}>
            {isCritical ? <ShieldCheck className="h-5 w-5" /> : <Cpu className="h-5 w-5" />}
          </div>
          <h4 className="font-semibold text-slate-800 text-base leading-tight">
            {competency.competency.replace(/_/g, " ").replace(/\w\S*/g, w => w.charAt(0).toUpperCase() + w.substring(1).toLowerCase())}
          </h4>
        </div>
        <EvidenceTrigger evidence={competency.evidence} title={`Evidence for ${competency.competency}`} />
      </div>

      <div className="flex items-center gap-3 mt-auto">
        <span className={`text-xs font-bold uppercase tracking-wider px-2 py-1 rounded-md ${
          isCritical ? 'bg-rose-100 text-rose-700' :
          isHigh ? 'bg-indigo-100 text-indigo-700' :
          'bg-slate-100 text-slate-700'
        }`}>
          {competency.importance} Importance
        </span>
        
        <span className="text-xs font-medium text-slate-500 flex items-center gap-1">
          Origin: <span className="text-slate-700">{competency.origin.replace(/_/g, " ")}</span>
        </span>
      </div>
    </div>
  );
}
