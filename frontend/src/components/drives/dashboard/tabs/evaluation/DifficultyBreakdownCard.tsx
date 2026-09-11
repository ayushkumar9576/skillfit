import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { Gauge, CheckCircle2 } from "lucide-react";

export default function DifficultyBreakdownCard() {
  const { snapshot } = useDriveSnapshot();
  const difficulty = snapshot?.intelligence_payload?.difficulty;

  if (!difficulty) {
    return (
      <EmptyIntelligenceCard
        title="No Difficulty Profile"
        description="Difficulty and competitive intelligence was not generated for this drive."
        icon={Gauge}
      />
    );
  }

  const getDifficultyColor = (level: string) => {
    switch (level) {
      case "BEGINNER": return "text-emerald-600 bg-emerald-50 border-emerald-200";
      case "MODERATE": return "text-blue-600 bg-blue-50 border-blue-200";
      case "COMPETITIVE": return "text-indigo-600 bg-indigo-50 border-indigo-200";
      case "HIGHLY_COMPETITIVE": return "text-purple-600 bg-purple-50 border-purple-200";
      case "ELITE": return "text-rose-600 bg-rose-50 border-rose-200";
      default: return "text-slate-600 bg-slate-50 border-slate-200";
    }
  };

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden h-full">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-2">
          <Gauge className="h-4 w-4 text-purple-500" />
          <h3 className="font-semibold text-slate-800">Difficulty Breakdown</h3>
        </div>
        <EvidenceTrigger evidence={difficulty.evidence} title="Difficulty Evidence" />
      </div>
      
      <div className="p-6 flex flex-col gap-6">
        
        <div className={`p-4 rounded-xl border flex flex-col items-center justify-center text-center ${getDifficultyColor(difficulty.level)}`}>
          <span className="text-xs font-bold uppercase tracking-wider opacity-80 mb-1">Overall Difficulty</span>
          <span className="text-2xl font-black tracking-tight">{difficulty.level.replace(/_/g, " ")}</span>
        </div>

        <div className="flex flex-col gap-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Key Driving Factors</h4>
          <ul className="space-y-3">
            {difficulty.difficulty_factors.map((factor, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <CheckCircle2 className="h-4 w-4 text-purple-400 mt-0.5 shrink-0" />
                <span className="text-sm text-slate-700 leading-snug">{factor}</span>
              </li>
            ))}
          </ul>
        </div>

        {difficulty.reasoning && (
          <div className="mt-2 p-4 bg-slate-50 border border-slate-100 rounded-lg">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 block">Engine Reasoning</span>
            <p className="text-sm text-slate-600 italic">"{difficulty.reasoning}"</p>
          </div>
        )}

      </div>
    </div>
  );
}
