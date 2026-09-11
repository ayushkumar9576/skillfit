import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import BehavioralCompetencyChip from "./BehavioralCompetencyChip";
import { Users } from "lucide-react";

export default function BehavioralCompetencySection() {
  const { snapshot } = useDriveSnapshot();
  const competencies = snapshot?.intelligence_payload?.behavioral_competencies;

  if (!competencies || competencies.length === 0) {
    return (
      <EmptyIntelligenceCard
        title="No Behavioral Competencies Detected"
        description="No behavioral expectations or soft skills were extracted from this snapshot."
        icon={Users}
      />
    );
  }

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden h-full">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <Users className="h-4 w-4 text-purple-500" />
        <h3 className="font-semibold text-slate-800">Behavioral Expectations</h3>
      </div>
      <div className="p-5 flex flex-wrap gap-3">
        {competencies.map((comp, idx) => (
          <BehavioralCompetencyChip key={`${comp.competency}-${idx}`} competency={comp} />
        ))}
      </div>
    </div>
  );
}
