import React from "react";
import { BehavioralCompetencyIntelligence } from "@/types/drives";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";

interface BehavioralCompetencyChipProps {
  competency: BehavioralCompetencyIntelligence;
}

export default function BehavioralCompetencyChip({ competency }: BehavioralCompetencyChipProps) {
  const name = competency.competency.replace(/_/g, " ").toLowerCase();
  
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg group hover:border-indigo-300 transition-colors">
      <span className="text-sm font-semibold text-slate-700 capitalize group-hover:text-indigo-700 transition-colors">
        {name}
      </span>
      <EvidenceTrigger evidence={competency.evidence} title={`Evidence for ${name}`} />
    </div>
  );
}
