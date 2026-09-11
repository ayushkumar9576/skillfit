import React, { useMemo } from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import SuccessIndicatorCard from "./SuccessIndicatorCard";
import { Trophy } from "lucide-react";

export default function SuccessIndicatorsGrid() {
  const { snapshot } = useDriveSnapshot();
  const indicators = snapshot?.intelligence_payload?.success_indicators;

  const sortedIndicators = useMemo(() => {
    if (!indicators) return [];
    
    const getWeight = (strength: string) => {
      switch (strength) {
        case "REQUIRED": return 3;
        case "PREFERRED": return 2;
        case "BONUS": return 1;
        default: return 0;
      }
    };

    return [...indicators].sort((a, b) => getWeight(b.strength) - getWeight(a.strength));
  }, [indicators]);

  if (!sortedIndicators || sortedIndicators.length === 0) {
    return (
      <EmptyIntelligenceCard
        title="No Success Indicators"
        description="The intelligence engine did not identify specific success patterns for this drive."
        icon={Trophy}
      />
    );
  }

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden h-full">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <Trophy className="h-4 w-4 text-amber-500" />
        <h3 className="font-semibold text-slate-800">Success Indicators</h3>
      </div>
      <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
        {sortedIndicators.map((ind, idx) => (
          <SuccessIndicatorCard key={`${ind.indicator}-${idx}`} indicator={ind} />
        ))}
      </div>
    </div>
  );
}
