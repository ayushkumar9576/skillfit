import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import TechnicalCompetencyCard from "./TechnicalCompetencyCard";
import { Cpu } from "lucide-react";

export default function TechnicalCompetencySection() {
  const { snapshot } = useDriveSnapshot();
  const competencies = snapshot?.intelligence_payload?.technical_competencies;

  if (!competencies || competencies.length === 0) {
    return (
      <EmptyIntelligenceCard
        title="No Technical Competencies Detected"
        description="The intelligence engine did not detect any evaluated technical skills or competencies for this role."
        icon={Cpu}
      />
    );
  }

  // Sort by importance (Critical > High > Medium > Low)
  const getWeight = (imp: string) => {
    switch (imp) {
      case "CRITICAL": return 4;
      case "HIGH": return 3;
      case "MEDIUM": return 2;
      case "LOW": return 1;
      default: return 0;
    }
  };

  const sorted = [...competencies].sort((a, b) => getWeight(b.importance) - getWeight(a.importance));

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden h-full">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <Cpu className="h-4 w-4 text-emerald-500" />
        <h3 className="font-semibold text-slate-800">Evaluated Technical Competencies</h3>
      </div>
      <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
        {sorted.map((comp, idx) => (
          <TechnicalCompetencyCard key={`${comp.competency}-${idx}`} competency={comp} />
        ))}
      </div>
    </div>
  );
}
