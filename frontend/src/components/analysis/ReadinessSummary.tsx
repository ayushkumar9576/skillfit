import { CheckCircle2, XCircle, TrendingUp } from "lucide-react";
import StateWrapper from "./StateWrapper";

// Inline type for now, can be moved to types later if needed globally
export interface ReadinessAnalysisResult {
  readiness_level: string;
  summary_text: string;
  strength_areas: string[];
  improvement_areas: string[];
}

interface ReadinessSummaryProps {
  result: ReadinessAnalysisResult;
  isLoading?: boolean;
  error?: Error | null;
}

export default function ReadinessSummary({
  result,
  isLoading = false,
  error = null,
}: ReadinessSummaryProps) {
  return (
    <StateWrapper
      isLoading={isLoading}
      error={error}
      isEmpty={!result}
      emptyTitle="No Readiness Data"
      emptyMessage="Placement readiness data could not be generated."
    >
      <div className="grid grid-cols-1 gap-6 md:grid-cols-12 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        {/* Readiness Level Card */}
        <div className="md:col-span-4 bg-indigo-50 p-6 flex flex-col justify-center items-center text-center border-b md:border-b-0 md:border-r border-slate-200">
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Placement Readiness</h3>
          
          <div className="inline-flex items-center justify-center h-24 w-24 rounded-full bg-white shadow-sm ring-4 ring-indigo-100 mb-4">
            <TrendingUp className="h-10 w-10 text-indigo-600" />
          </div>
          
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-100 px-4 py-1.5 text-base font-bold text-indigo-800">
            {result?.readiness_level || "UNKNOWN"}
          </div>

          <p className="text-sm text-slate-600 mt-4 leading-relaxed font-medium px-2">
            {result?.summary_text}
          </p>
        </div>

        {/* Strengths & Gaps */}
        <div className="md:col-span-8 p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-4">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              </span>
              Strength Areas
            </h4>
            <ul className="space-y-3">
              {result?.strength_areas && result.strength_areas.length > 0 ? result.strength_areas.map((strength, i) => (
                <li key={i} className="flex gap-2 text-sm text-slate-600">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span>{strength}</span>
                </li>
              )) : (
                <li className="text-sm text-slate-400 italic">No specific strengths identified.</li>
              )}
            </ul>
          </div>
          
          <div>
            <h4 className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-4">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-100">
                <XCircle className="h-4 w-4 text-red-600" />
              </span>
              Improvement Areas
            </h4>
            <ul className="space-y-3">
              {result?.improvement_areas && result.improvement_areas.length > 0 ? result.improvement_areas.map((gap, i) => (
                <li key={i} className="flex gap-2 text-sm text-slate-600">
                  <XCircle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{gap}</span>
                </li>
              )) : (
                <li className="text-sm text-slate-400 italic">No significant improvement areas identified.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </StateWrapper>
  );
}
