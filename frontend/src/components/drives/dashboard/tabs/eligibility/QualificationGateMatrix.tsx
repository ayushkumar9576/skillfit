import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import QualificationRow from "./QualificationRow";
import { UserCheck } from "lucide-react";

export default function QualificationGateMatrix() {
  const { snapshot } = useDriveSnapshot();
  const qualifications = snapshot?.intelligence_payload?.qualifications;

  if (!qualifications || qualifications.length === 0) {
    return (
      <EmptyIntelligenceCard
        title="No Explicit Qualifications Detected"
        description="The intelligence engine did not identify strict eligibility criteria for this drive."
        icon={UserCheck}
      />
    );
  }

  const hardGates = qualifications.filter(q => q.is_mandatory);
  const preferences = qualifications.filter(q => !q.is_mandatory);

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden h-full">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <UserCheck className="h-4 w-4 text-indigo-500" />
        <h3 className="font-semibold text-slate-800">Eligibility & Qualifications Matrix</h3>
      </div>
      
      <div className="p-5 flex flex-col gap-6">
        
        {hardGates.length > 0 && (
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-rose-600 border-b border-rose-100 pb-2">
              Mandatory Requirements (Hard Gates)
            </h4>
            <div className="flex flex-col gap-2">
              {hardGates.map((qual, idx) => (
                <QualificationRow key={`hard-${idx}`} qualification={qual} isHardGate={true} />
              ))}
            </div>
          </div>
        )}

        {preferences.length > 0 && (
          <div className="flex flex-col gap-3 mt-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-blue-600 border-b border-blue-100 pb-2">
              Preferred Qualifications (Soft Preferences)
            </h4>
            <div className="flex flex-col gap-2">
              {preferences.map((qual, idx) => (
                <QualificationRow key={`pref-${idx}`} qualification={qual} isHardGate={false} />
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
