import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import { Code2, Cpu, Wrench, Users } from "lucide-react";

export default function TechnologySummaryBanner() {
  const { snapshot } = useDriveSnapshot();
  const technologies = snapshot?.intelligence_payload?.technologies || [];
  const techComps = snapshot?.intelligence_payload?.technical_competencies || [];
  const behavComps = snapshot?.intelligence_payload?.behavioral_competencies || [];

  const mandatoryTechs = technologies.filter((t) => t.is_mandatory === true).length;
  const preferredTechs = technologies.filter((t) => t.is_mandatory === false).length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-white border border-slate-200 rounded-xl p-4 shadow-sm mb-6">
      
      <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-50 transition-colors">
        <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
          <Code2 className="h-5 w-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-2xl font-bold text-slate-800 leading-none">{mandatoryTechs}</span>
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider mt-1">Mandatory Tech</span>
        </div>
      </div>

      <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-50 transition-colors">
        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
          <Wrench className="h-5 w-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-2xl font-bold text-slate-800 leading-none">{preferredTechs}</span>
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider mt-1">Preferred Tech</span>
        </div>
      </div>

      <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-50 transition-colors border-t md:border-t-0 md:border-l border-slate-100">
        <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
          <Cpu className="h-5 w-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-2xl font-bold text-slate-800 leading-none">{techComps.length}</span>
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider mt-1">Tech Skills</span>
        </div>
      </div>

      <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-50 transition-colors border-t md:border-t-0 md:border-l border-slate-100">
        <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
          <Users className="h-5 w-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-2xl font-bold text-slate-800 leading-none">{behavComps.length}</span>
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider mt-1">Soft Skills</span>
        </div>
      </div>

    </div>
  );
}
