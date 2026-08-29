import { AlertTriangle } from "lucide-react";
import StateWrapper from "./StateWrapper";
import { Finding, FindingType, FindingSeverity } from "@/types/candidate-profile";

interface MissingEvidencePanelProps {
  findings: Finding[];
  isLoading?: boolean;
  error?: Error | null;
}

export default function MissingEvidencePanel({
  findings,
  isLoading = false,
  error = null,
}: MissingEvidencePanelProps) {
  // Filter for only missing signals
  const missingEvidence = (findings || []).filter(f => f.type === FindingType.MISSING_SIGNAL);

  return (
    <StateWrapper
      isLoading={isLoading}
      error={error}
      isEmpty={!missingEvidence || missingEvidence.length === 0}
      emptyTitle="No Missing Evidence"
      emptyMessage="Your resume contains strong evidence across all expected dimensions."
    >
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 shadow-sm">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-red-900 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            Missing Evidence Findings
          </h3>
          <p className="text-sm text-red-700 mt-1">
            Important components missing from your resume that are impacting your readiness.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {missingEvidence.map((item, index) => (
            <div key={index} className="rounded-lg bg-white p-4 shadow-sm border border-red-100 flex flex-col h-full">
              <div className="mb-2 flex items-start justify-between gap-2">
                <h4 className="font-bold text-slate-900">{item.title}</h4>
                <span className={`shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                  item.severity === FindingSeverity.CRITICAL ? "bg-red-100 text-red-800" :
                  item.severity === FindingSeverity.HIGH ? "bg-orange-100 text-orange-800" :
                  item.severity === FindingSeverity.MEDIUM ? "bg-amber-100 text-amber-800" :
                  "bg-slate-100 text-slate-800"
                }`}>
                  {item.severity}
                </span>
              </div>
              <div className="flex-1 mt-1">
                <p className="text-slate-600 text-sm">{item.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </StateWrapper>
  );
}
