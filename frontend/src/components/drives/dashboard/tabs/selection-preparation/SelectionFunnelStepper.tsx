import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import SelectionRoundCard from "./SelectionRoundCard";
import { ListOrdered } from "lucide-react";

export default function SelectionFunnelStepper() {
  const { snapshot } = useDriveSnapshot();
  const process = snapshot?.intelligence_payload?.selection_process;

  if (!process || process.length === 0) {
    return (
      <EmptyIntelligenceCard
        title="No Selection Process Detected"
        description="The intelligence engine did not identify specific selection rounds for this drive."
        icon={ListOrdered}
      />
    );
  }

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <ListOrdered className="h-4 w-4 text-indigo-500" />
        <h3 className="font-semibold text-slate-800">Selection Funnel</h3>
      </div>
      
      <div className="p-6 md:p-8 flex flex-col md:flex-row items-stretch md:items-start overflow-x-auto gap-4 md:gap-0">
        {process.map((round, idx) => (
          <SelectionRoundCard 
            key={`${round.round_name}-${idx}`} 
            round={round} 
            index={idx} 
            totalRounds={process.length} 
          />
        ))}
      </div>
    </div>
  );
}
