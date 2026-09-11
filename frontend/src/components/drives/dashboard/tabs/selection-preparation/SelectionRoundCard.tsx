import React, { memo } from "react";
import { SelectionProcessIntelligence } from "@/types/drives";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";

interface SelectionRoundCardProps {
  round: SelectionProcessIntelligence;
  index: number;
  totalRounds: number;
}

const SelectionRoundCard = memo(function SelectionRoundCard({ round, index, totalRounds }: SelectionRoundCardProps) {
  const isCritical = round.importance === "CRITICAL";

  return (
    <div className="relative flex flex-col group min-w-[200px] flex-1">
      {/* Desktop Line Connector */}
      {index < totalRounds - 1 && (
        <div className="hidden md:block absolute top-6 left-[50%] w-full h-[2px] bg-slate-200 z-0 group-hover:bg-indigo-200 transition-colors" />
      )}
      
      {/* Mobile Line Connector */}
      {index < totalRounds - 1 && (
        <div className="md:hidden absolute left-10 top-12 w-[2px] h-full bg-slate-200 z-0" />
      )}

      <div className="flex md:flex-col items-center gap-4 relative z-10 p-4 rounded-xl hover:bg-slate-50 transition-colors">
        
        {/* Step Indicator */}
        <div className={`w-12 h-12 rounded-full border-4 flex items-center justify-center font-bold text-lg bg-white shrink-0 ${
          isCritical ? "border-rose-500 text-rose-600" : "border-indigo-500 text-indigo-600"
        }`}>
          {index + 1}
        </div>

        {/* Content */}
        <div className="flex flex-col md:items-center gap-1.5 md:text-center w-full">
          <h4 className="font-bold text-slate-800 leading-tight">
            {round.round_name}
          </h4>
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            {round.round_type.replace(/_/g, " ")}
          </span>
          
          <div className="flex flex-wrap md:justify-center items-center gap-2 mt-2">
            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
              isCritical ? "bg-rose-100 text-rose-700" :
              round.importance === "HIGH" ? "bg-orange-100 text-orange-700" :
              "bg-slate-100 text-slate-700"
            }`}>
              {round.importance} Priority
            </span>
            <EvidenceTrigger evidence={round.evidence} title={`Evidence for ${round.round_name}`} />
          </div>
        </div>
      </div>
    </div>
  );
});

export default SelectionRoundCard;
