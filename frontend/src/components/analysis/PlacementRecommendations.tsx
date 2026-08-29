import { Briefcase, ArrowRight, Zap, Target } from "lucide-react";
import StateWrapper from "./StateWrapper";
import { Recommendation } from "@/types/candidate-profile";

interface PlacementRecommendationsProps {
  recommendations: Recommendation[];
  isLoading?: boolean;
  error?: Error | null;
}

export default function PlacementRecommendations({
  recommendations,
  isLoading = false,
  error = null,
}: PlacementRecommendationsProps) {
  // Sort by priority (HIGH > MEDIUM > LOW)
  const sortedRecommendations = [...(recommendations || [])].sort((a, b) => {
    const priorityWeight: Record<string, number> = { HIGH: 3, MEDIUM: 2, LOW: 1 };
    return (priorityWeight[b.priority?.toUpperCase()] || 0) - (priorityWeight[a.priority?.toUpperCase()] || 0);
  });

  return (
    <StateWrapper
      isLoading={isLoading}
      error={error}
      isEmpty={!recommendations || recommendations.length === 0}
      emptyTitle="No Actionable Recommendations"
      emptyMessage="Your profile is well-aligned with current targets. Keep building your portfolio!"
    >
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Briefcase className="h-5 w-5 text-indigo-500" />
            Actionable Recommendations
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            Targeted steps to improve your profile based on intelligence findings.
          </p>
        </div>

        <div className="space-y-4">
          {sortedRecommendations.map((rec, index) => (
            <div key={index} className="rounded-lg border border-slate-200 bg-slate-50 p-5">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-bold text-slate-900">{rec.title}</h4>
                    <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold ring-1 ring-inset ${
                      rec.priority?.toUpperCase() === 'HIGH' ? 'bg-red-50 text-red-700 ring-red-600/20' :
                      rec.priority?.toUpperCase() === 'MEDIUM' ? 'bg-amber-50 text-amber-700 ring-amber-600/20' :
                      'bg-slate-100 text-slate-700 ring-slate-600/20'
                    }`}>
                      {rec.priority?.toUpperCase()} PRIORITY
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mb-4">{rec.description}</p>
                  
                  {rec.derived_from && rec.derived_from.length > 0 && (
                    <div className="mb-3">
                      <span className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                        Derived From
                      </span>
                      <ul className="space-y-1">
                        {rec.derived_from.map((finding, idx) => (
                          <li key={idx} className="flex items-start gap-1.5 text-xs text-slate-600">
                            <ArrowRight className="h-3.5 w-3.5 mt-0.5 text-slate-400 shrink-0" />
                            {finding}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                <div className="sm:w-48 shrink-0 flex flex-col gap-3 border-t sm:border-t-0 sm:border-l border-slate-200 pt-4 sm:pt-0 sm:pl-4">
                  <div>
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                      <Zap className="h-3.5 w-3.5" /> Impact
                    </span>
                    <span className="text-sm font-medium text-slate-700">{rec.estimated_impact}</span>
                  </div>
                  
                  {rec.target_competencies && rec.target_competencies.length > 0 && (
                    <div>
                      <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                        <Target className="h-3.5 w-3.5" /> Targets
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {rec.target_competencies.map((comp, idx) => (
                          <span key={idx} className="inline-flex items-center rounded bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-600 border border-slate-200">
                            {comp}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </StateWrapper>
  );
}
