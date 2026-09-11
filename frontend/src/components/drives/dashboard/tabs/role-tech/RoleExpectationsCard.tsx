import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { CheckSquare, Briefcase } from "lucide-react";
import { ImportanceLevel } from "@/types/drives";

export default function RoleExpectationsCard() {
  const { snapshot } = useDriveSnapshot();
  const expectations = snapshot?.intelligence_payload?.role_expectations;

  if (!expectations || expectations.length === 0) {
    return (
      <EmptyIntelligenceCard
        title="No Role Expectations Available"
        description="This snapshot does not contain explicit role expectation intelligence."
        icon={Briefcase}
      />
    );
  }

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <CheckSquare className="h-4 w-4 text-blue-500" />
        <h3 className="font-semibold text-slate-800">Role Expectations</h3>
      </div>
      
      <div className="p-5">
        <ul className="space-y-4">
          {expectations.map((exp, idx) => {
            const isCritical = exp.importance === ImportanceLevel.critical;
            return (
              <li key={idx} className="flex items-start gap-3">
                <div className={`mt-0.5 rounded-sm h-4 w-4 flex items-center justify-center border shrink-0 ${
                  isCritical ? 'border-rose-500 bg-rose-50 text-rose-500' : 'border-indigo-500 bg-indigo-50 text-indigo-500'
                }`}>
                  <CheckSquare className="h-3 w-3" />
                </div>
                <div className="flex flex-col flex-1 gap-1">
                  <span className="text-sm text-slate-700 leading-snug">{exp.expectation}</span>
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                      isCritical ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {exp.importance} Priority
                    </span>
                    <EvidenceTrigger evidence={exp.evidence} title="Expectation Evidence" />
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
