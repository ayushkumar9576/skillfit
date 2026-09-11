import React, { useMemo } from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import RiskCard from "./RiskCard";
import { ShieldAlert } from "lucide-react";

export default function RiskBreakdownSection() {
  const { snapshot } = useDriveSnapshot();
  const risks = snapshot?.intelligence_payload?.risks;

  const sortedRisks = useMemo(() => {
    if (!risks) return [];
    
    const getWeight = (sev: string) => {
      switch (sev) {
        case "CRITICAL": return 4;
        case "HIGH": return 3;
        case "MEDIUM": return 2;
        case "LOW": return 1;
        default: return 0;
      }
    };

    return [...risks].sort((a, b) => getWeight(b.severity) - getWeight(a.severity));
  }, [risks]);

  if (!sortedRisks || sortedRisks.length === 0) {
    return (
      <EmptyIntelligenceCard
        title="No Major Risks Identified"
        description="The engine did not identify any unusual or high-severity risks associated with this drive."
        icon={ShieldAlert}
      />
    );
  }

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden h-full">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <ShieldAlert className="h-4 w-4 text-rose-500" />
        <h3 className="font-semibold text-slate-800">Risk Assessment</h3>
      </div>
      <div className="p-5 flex flex-col gap-4">
        {sortedRisks.map((risk, idx) => (
          <RiskCard key={`${risk.risk}-${idx}`} risk={risk} />
        ))}
      </div>
    </div>
  );
}
