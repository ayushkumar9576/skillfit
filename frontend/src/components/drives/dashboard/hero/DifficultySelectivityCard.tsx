import React from "react";
import { useDriveSnapshot } from "../../context/SnapshotProvider";
import { Gauge, Info } from "lucide-react";
import { DriveDifficultyLevel } from "@/types/drives";

// Reusable pure CSS/SVG meter component internal to this card (could be moved to shared if needed elsewhere)
const DifficultyMeter = ({ level }: { level: DriveDifficultyLevel }) => {
  const getLevelConfig = () => {
    switch (level) {
      case DriveDifficultyLevel.beginner: return { value: 20, color: "text-emerald-500", label: "Beginner" };
      case DriveDifficultyLevel.moderate: return { value: 40, color: "text-blue-500", label: "Moderate" };
      case DriveDifficultyLevel.competitive: return { value: 60, color: "text-indigo-500", label: "Competitive" };
      case DriveDifficultyLevel.highly_competitive: return { value: 80, color: "text-purple-500", label: "Highly Competitive" };
      case DriveDifficultyLevel.elite: return { value: 100, color: "text-rose-500", label: "Elite" };
      default: return { value: 0, color: "text-slate-300", label: "Unknown" };
    }
  };

  const config = getLevelConfig();
  
  return (
    <div className="flex flex-col items-center justify-center relative my-4">
      <svg className="w-32 h-16" viewBox="0 0 100 50">
        {/* Background track (semi-circle) */}
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke="#f1f5f9"
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Foreground track representing the level */}
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke="currentColor"
          strokeWidth="12"
          strokeLinecap="round"
          className={config.color}
          strokeDasharray="125.6" /* Circumference of half circle with r=40 is ~125.6 */
          strokeDashoffset={125.6 - (125.6 * config.value) / 100}
        />
      </svg>
      <div className="absolute bottom-0 text-center">
        <span className={`text-sm font-bold uppercase tracking-wider ${config.color}`}>
          {config.label}
        </span>
      </div>
    </div>
  );
};

export default function DifficultySelectivityCard() {
  const { snapshot } = useDriveSnapshot();
  const difficulty = snapshot?.intelligence_payload?.difficulty;

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm hover:shadow transition-shadow">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50/50">
        <Gauge className="h-4 w-4 text-purple-500" />
        <h3 className="font-semibold text-slate-800">Difficulty & Selectivity</h3>
      </div>
      
      <div className="p-5 flex-1 flex flex-col">
        {!difficulty ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
            <Info className="h-8 w-8 text-slate-300 mb-2" />
            <p className="text-sm font-medium text-slate-500">Not Available In Snapshot Version</p>
            <p className="text-xs text-slate-400 mt-1">Requires schema v1.3+</p>
          </div>
        ) : (
          <div className="space-y-4">
            <DifficultyMeter level={difficulty.level} />
            
            {difficulty.difficulty_factors && difficulty.difficulty_factors.length > 0 && (
              <div className="mt-6">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Key Factors</h4>
                <ul className="space-y-2">
                  {difficulty.difficulty_factors.slice(0, 3).map((factor, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-slate-600">
                      <span className="text-purple-500 mt-0.5 font-bold">•</span>
                      <span className="leading-tight">{factor}</span>
                    </li>
                  ))}
                  {difficulty.difficulty_factors.length > 3 && (
                    <li className="text-xs text-slate-400 italic pl-3">
                      + {difficulty.difficulty_factors.length - 3} more factors
                    </li>
                  )}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
