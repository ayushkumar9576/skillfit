import { Map, ArrowRight, CornerDownRight } from "lucide-react";
import StateWrapper from "./StateWrapper";
import { Recommendation } from "@/types/candidate-profile";

interface ImprovementRoadmapProps {
  recommendations: Recommendation[];
  isLoading?: boolean;
  error?: Error | null;
}

export default function ImprovementRoadmap({
  recommendations,
  isLoading = false,
  error = null,
}: ImprovementRoadmapProps) {
  // Sort by priority (HIGH > MEDIUM > LOW) to create the roadmap
  const roadmap = [...(recommendations || [])].sort((a, b) => {
    const priorityWeight: Record<string, number> = { HIGH: 3, MEDIUM: 2, LOW: 1 };
    return (priorityWeight[b.priority?.toUpperCase()] || 0) - (priorityWeight[a.priority?.toUpperCase()] || 0);
  });

  return (
    <StateWrapper
      isLoading={isLoading}
      error={error}
      isEmpty={!roadmap || roadmap.length === 0}
      emptyTitle="No Improvements Needed"
      emptyMessage="Your profile is currently fully optimized based on evidence."
    >
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Map className="h-5 w-5 text-indigo-500" />
            Improvement Roadmap
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            Prioritized actions to strengthen your intelligence profile.
          </p>
        </div>

        <div className="space-y-4">
          {roadmap.map((item, idx) => (
            <div key={idx} className="flex flex-col p-4 rounded-lg border border-slate-100 bg-slate-50 hover:bg-slate-100/80 transition-colors group gap-3">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white font-bold text-slate-700 shadow-sm border border-slate-200 mt-0.5">
                    {idx + 1}
                  </div>
                  <div>
                    <span className="font-bold text-slate-800 group-hover:text-indigo-700 transition-colors block mb-1">
                      {item.title}
                    </span>
                    <p className="text-sm text-slate-600">
                      {item.description}
                    </p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2 shrink-0">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    item.priority?.toUpperCase() === 'HIGH' ? 'bg-red-100 text-red-700' :
                    item.priority?.toUpperCase() === 'MEDIUM' ? 'bg-amber-100 text-amber-700' :
                    'bg-slate-200 text-slate-700'
                  }`}>
                    {item.priority?.toUpperCase()} PRIORITY
                  </span>
                  <span className="text-xs font-medium text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200 shadow-sm">
                    Impact: {item.estimated_impact}
                  </span>
                </div>
              </div>

              {item.derived_from && item.derived_from.length > 0 && (
                <div className="ml-12 pl-4 border-l-2 border-indigo-100">
                  <span className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    <CornerDownRight className="h-3 w-3" /> Derived From
                  </span>
                  <ul className="space-y-1">
                    {item.derived_from.map((finding, fIdx) => (
                      <li key={fIdx} className="flex items-start gap-1.5 text-xs text-slate-500">
                        <ArrowRight className="h-3.5 w-3.5 mt-0.5 text-slate-300 shrink-0" />
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </StateWrapper>
  );
}
