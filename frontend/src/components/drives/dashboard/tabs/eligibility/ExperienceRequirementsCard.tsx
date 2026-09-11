import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { GraduationCap } from "lucide-react";

export default function ExperienceRequirementsCard() {
  const { snapshot } = useDriveSnapshot();
  const exp = snapshot?.intelligence_payload?.experience_requirements;

  if (!exp) {
    return (
      <EmptyIntelligenceCard
        title="No Experience Requirements"
        description="Experience criteria was not identified in this snapshot."
        icon={GraduationCap}
      />
    );
  }

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-emerald-500" />
          <h3 className="font-semibold text-slate-800">Experience Requirements</h3>
        </div>
        <EvidenceTrigger evidence={exp.evidence} title="Experience Evidence" />
      </div>
      
      <div className="p-5 flex flex-col gap-4">
        {exp.freshers_eligible ? (
          <div className="bg-emerald-50 border border-emerald-100 text-emerald-800 px-4 py-3 rounded-lg flex items-center gap-3">
            <div className="flex flex-col">
              <span className="font-bold text-lg leading-tight">Freshers Eligible</span>
              <span className="text-emerald-600 text-sm mt-0.5">Students graduating in current cycle can apply</span>
            </div>
          </div>
        ) : (
          <div className="bg-orange-50 border border-orange-100 text-orange-800 px-4 py-3 rounded-lg flex items-center gap-3">
            <div className="flex flex-col">
              <span className="font-bold text-lg leading-tight">Experience Required</span>
              <span className="text-orange-600 text-sm mt-0.5">Freshers are generally not eligible</span>
            </div>
          </div>
        )}

        {(exp.min_experience_years !== null || exp.max_experience_years !== null) && (
          <div className="flex items-center justify-between py-2 border-t border-slate-100 mt-2">
            <span className="text-sm font-medium text-slate-500">Experience Range</span>
            <span className="font-bold text-slate-800">
              {exp.min_experience_years ?? 0} — {exp.max_experience_years ?? "Any"} Years
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
