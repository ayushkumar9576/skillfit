import { Globe, GitMerge, BookOpen } from "lucide-react";
import StateWrapper from "./StateWrapper";
import { DomainIntelligence } from "@/types/candidate-profile";
import EvidenceSourceBadge from "@/components/shared/EvidenceSourceBadge";

interface DomainIntelligenceOverviewProps {
  domains: DomainIntelligence[];
  isLoading?: boolean;
  error?: Error | null;
}

export default function DomainIntelligenceOverview({
  domains,
  isLoading = false,
  error = null,
}: DomainIntelligenceOverviewProps) {
  return (
    <StateWrapper
      isLoading={isLoading}
      error={error}
      isEmpty={!domains || domains.length === 0}
      emptyTitle="No Domains Identified"
      emptyMessage="Not enough evidence to associate with specific industry domains."
    >
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm h-full">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Globe className="h-5 w-5 text-indigo-500" />
            Domain Intelligence Overview
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            Industry domains supported by your technical competencies and verified evidence.
          </p>
        </div>

        <div className="space-y-5">
          {domains?.map((domain, index) => (
            <div key={index} className="rounded-lg border border-slate-200 bg-slate-50/50 p-4">
              <h4 className="font-bold text-slate-900 mb-4 pb-2 border-b border-slate-200">
                {typeof domain.domain === "string" ? domain.domain.replace(/_/g, ' ') : "Unknown Domain"}
              </h4>

              <div className="space-y-4">
                {domain.supporting_competencies && domain.supporting_competencies.length > 0 && (
                  <div>
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                      <BookOpen className="h-3.5 w-3.5" /> Supporting Competencies
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {domain.supporting_competencies.map((comp, idx) => (
                        <span key={idx} className="inline-flex items-center rounded-md bg-white px-2 py-1 text-xs font-medium text-slate-700 ring-1 ring-inset ring-slate-200 shadow-sm">
                          {comp}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {domain.supporting_technologies && domain.supporting_technologies.length > 0 && (
                  <div>
                    <span className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                      <GitMerge className="h-3.5 w-3.5" /> Supporting Technologies
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {domain.supporting_technologies.map((tech, idx) => (
                        <span key={idx} className="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600 ring-1 ring-inset ring-slate-200">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {domain.evidence && domain.evidence.length > 0 && (
                  <div className="pt-2 border-t border-slate-200/60 mt-4">
                    <span className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                      Evidence Sources
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {Array.from(new Set(domain.evidence.map(e => e.source))).map(src => (
                        <EvidenceSourceBadge key={src} source={src} />
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
