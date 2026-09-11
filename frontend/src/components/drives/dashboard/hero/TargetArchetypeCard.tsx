import React from "react";
import { useDriveSnapshot } from "../../context/SnapshotProvider";
import { Users, Info } from "lucide-react";

export default function TargetArchetypeCard() {
  const { snapshot } = useDriveSnapshot();
  const relevance = snapshot?.intelligence_payload?.placement_relevance;

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm hover:shadow transition-shadow">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50/50">
        <Users className="h-4 w-4 text-indigo-500" />
        <h3 className="font-semibold text-slate-800">Target Archetype</h3>
      </div>
      
      <div className="p-5 flex-1 flex flex-col">
        {!relevance ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
            <Info className="h-8 w-8 text-slate-300 mb-2" />
            <p className="text-sm font-medium text-slate-500">Not Available In Snapshot Version</p>
            <p className="text-xs text-slate-400 mt-1">Requires schema v1.3+</p>
          </div>
        ) : (
          <div className="space-y-5">
            {relevance.target_candidate_profiles && relevance.target_candidate_profiles.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Primary Profiles</h4>
                <div className="flex flex-wrap gap-2">
                  {relevance.target_candidate_profiles.map((profile, idx) => (
                    <span 
                      key={idx} 
                      className="inline-flex px-2.5 py-1 rounded-md text-sm font-medium bg-indigo-50 text-indigo-700 border border-indigo-100"
                    >
                      {profile}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {relevance.preferred_backgrounds && relevance.preferred_backgrounds.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Preferred Backgrounds</h4>
                <div className="flex flex-wrap gap-2">
                  {relevance.preferred_backgrounds.map((bg, idx) => (
                    <span 
                      key={idx} 
                      className="inline-flex px-2.5 py-1 rounded-md text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200"
                    >
                      {bg}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {(!relevance.target_candidate_profiles?.length && !relevance.preferred_backgrounds?.length) && (
              <p className="text-sm text-slate-500 italic">No specific archetypes identified.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
