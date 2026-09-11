import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import { Target } from "lucide-react";

export default function KeyEvaluationFocusBanner() {
  const { snapshot } = useDriveSnapshot();
  const focusAreas = snapshot?.intelligence_payload?.preparation?.key_evaluation_focus;

  if (!focusAreas || focusAreas.length === 0) return null;

  return (
    <div className="bg-indigo-600 rounded-xl p-5 shadow-sm text-white relative overflow-hidden">
      {/* Background decoration */}
      <Target className="absolute -right-6 -bottom-6 w-32 h-32 text-indigo-500 opacity-20" />
      
      <div className="relative z-10 flex flex-col md:flex-row md:items-center gap-4">
        <div className="flex items-center gap-2 md:w-1/4 shrink-0">
          <Target className="h-5 w-5 text-indigo-200" />
          <h3 className="font-semibold text-lg">Key Evaluation Focus</h3>
        </div>
        
        <div className="flex flex-wrap gap-2 flex-1">
          {focusAreas.map((area, idx) => (
            <span 
              key={idx} 
              className="inline-flex px-3 py-1.5 rounded-lg text-sm font-medium bg-indigo-500/50 border border-indigo-400 text-indigo-50 backdrop-blur-sm shadow-sm"
            >
              {area}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
