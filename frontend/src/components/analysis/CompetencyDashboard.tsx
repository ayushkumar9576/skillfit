import { BrainCircuit } from "lucide-react";
import StateWrapper from "./StateWrapper";
import type { CompetencyIntelligence } from "@/types/candidate-profile";
import DemonstrationLevelBadge from "@/components/shared/DemonstrationLevelBadge";

interface CompetencyDashboardProps {
  competencies: CompetencyIntelligence[];
  isLoading?: boolean;
  error?: Error | null;
}

export default function CompetencyDashboard({
  competencies,
  isLoading = false,
  error = null,
}: CompetencyDashboardProps) {
  // Sorting could be based on level, but we'll leave them in API order for now
  const sortedCompetencies = [...(competencies || [])];

  return (
    <StateWrapper
      isLoading={isLoading}
      error={error}
      isEmpty={!competencies || competencies.length === 0}
      emptyTitle="No Competencies Assessed"
      emptyMessage="Not enough evidence was found to evaluate abstract competencies."
    >
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-indigo-500" />
            Competency Dashboard
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            Abstract skills derived from underlying technology and project evidence.
          </p>
        </div>

        <div className="space-y-6">
          {sortedCompetencies.map((comp) => (
            <div key={comp.competency} className="flex flex-col gap-3 pb-4 border-b border-slate-100 last:border-0">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-slate-900">{comp.competency}</h4>
                  <div className="mt-1">
                    <DemonstrationLevelBadge level={comp.demonstration_level} />
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                {comp.supporting_technologies && comp.supporting_technologies.length > 0 && (
                  <div>
                    <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
                      Supporting Technologies
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {comp.supporting_technologies.map(tech => (
                        <span key={tech} className="inline-flex items-center rounded-md bg-slate-50 px-2 py-1 text-xs font-medium text-slate-600 ring-1 ring-inset ring-slate-500/10">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {comp.supporting_projects && comp.supporting_projects.length > 0 && (
                  <div>
                    <span className="block text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
                      Demonstrated In
                    </span>
                    <div className="flex flex-col gap-1">
                      {comp.supporting_projects.map(proj => (
                        <span key={proj} className="text-slate-700">
                          • {proj}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </StateWrapper>
  );
}
