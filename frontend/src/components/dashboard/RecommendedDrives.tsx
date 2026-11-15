"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRecommendedDrives, RecommendedDrive } from "@/lib/api/matching";
import Card from "@/components/shared/Card";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";
import DetailedScoreBreakdownModal from "@/components/dashboard/DetailedScoreBreakdownModal";
import { parseApiError } from "@/lib/utils";
import { Building2, CheckCircle2, XCircle, ChevronRight, BarChart3, AlertTriangle } from "lucide-react";

export default function RecommendedDrives() {
  const [selectedDrive, setSelectedDrive] = useState<RecommendedDrive | null>(null);

  const { data: drives, isLoading, error, refetch } = useQuery({
    queryKey: ["recommendedDrives"],
    queryFn: () => getRecommendedDrives(),
  });

  if (isLoading) {
    return <LoadingState message="Loading recommended drives..." />;
  }

  if (error) {
    return <ErrorState message={parseApiError(error).message} retryAction={() => refetch()} />;
  }

  if (!drives || drives.length === 0) {
    return (
      <Card className="p-8 text-center text-slate-500">
        No matching drives available at the moment.
      </Card>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 gap-4">
        {drives.map((drive: RecommendedDrive) => (
          <Card 
            key={drive.drive_id} 
            className="p-5 sm:p-6 flex flex-col justify-between gap-4 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer group w-full"
            onClick={() => setSelectedDrive(drive)}
          >
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div>
                  <h3 className="font-bold text-lg text-slate-900 group-hover:text-indigo-600 transition-colors">
                    {drive.drive_title}
                  </h3>
                  <div className="flex items-center text-slate-500 text-sm mt-1">
                    <Building2 className="w-4 h-4 mr-1.5 text-slate-400 shrink-0" />
                    <span className="font-medium">{drive.company_name || "Unknown Company"}</span>
                  </div>
                </div>
                <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-1.5 shrink-0">
                  <div className="flex items-center gap-1.5">
                    {drive.is_eligible === false ? (
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold tracking-wide bg-rose-100 text-rose-800 border border-rose-200">
                        Not Eligible
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold tracking-wide bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Eligible
                      </span>
                    )}
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide ${
                      drive.tier === "EXCELLENT_MATCH" ? "bg-emerald-100 text-emerald-800" :
                      drive.tier === "STRONG_MATCH" ? "bg-indigo-100 text-indigo-800" :
                      drive.tier === "MODERATE_MATCH" ? "bg-amber-100 text-amber-800" :
                      "bg-red-100 text-red-800"
                    }`}>
                      {drive.tier.replace("_MATCH", "")}
                    </span>
                  </div>
                  <div className="text-xl sm:text-2xl font-bold text-slate-800">
                    {Math.round(drive.score * 100)}% Match
                  </div>
                </div>
              </div>

              <div className="text-sm text-slate-600 bg-slate-50 p-3.5 rounded-xl border border-slate-100/80 leading-relaxed">
                {drive.overall_narrative}
              </div>

              {drive.is_eligible === false && (
                <div className="text-xs text-rose-700 bg-rose-50/90 p-3 rounded-xl border border-rose-200/80 flex flex-col gap-1.5">
                  <div className="font-semibold flex items-center gap-1.5 text-rose-800">
                    <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
                    Academic Eligibility Criteria Not Met:
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-rose-600 pl-1">
                    {drive.eligibility_reasons && drive.eligibility_reasons.length > 0 ? (
                      drive.eligibility_reasons.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))
                    ) : (
                      <li>Does not satisfy mandatory academic criteria for this drive.</li>
                    )}
                  </ul>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                <div className="bg-emerald-50/30 p-3.5 rounded-xl border border-emerald-100/60">
                  <h4 className="text-xs font-semibold text-emerald-800 uppercase mb-2 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Top Strengths
                  </h4>
                  <ul className="space-y-1.5">
                    {drive.strengths.length > 0 ? drive.strengths.map((str, idx) => (
                      <li key={idx} className="flex items-start text-xs text-slate-700 font-medium">
                        <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 mr-2 shrink-0" />
                        <span>{str}</span>
                      </li>
                    )) : <li className="text-xs text-slate-400">None</li>}
                  </ul>
                </div>
                <div className="bg-rose-50/30 p-3.5 rounded-xl border border-rose-100/60">
                  <h4 className="text-xs font-semibold text-rose-800 uppercase mb-2 flex items-center gap-1.5">
                    <XCircle className="w-3.5 h-3.5 text-rose-600" />
                    Key Gaps
                  </h4>
                  <ul className="space-y-1.5">
                    {drive.gaps.length > 0 ? drive.gaps.map((gap, idx) => (
                      <li key={idx} className="flex items-start text-xs text-slate-700 font-medium">
                        <span className="inline-block w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 mr-2 shrink-0" />
                        <span>{gap}</span>
                      </li>
                    )) : <li className="text-xs text-slate-400">None</li>}
                  </ul>
                </div>
              </div>
            </div>

            {/* Action link */}
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-indigo-600 group-hover:text-indigo-700">
              <span className="flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4" />
                View Dimension-by-Dimension Score Breakdown
              </span>
              <ChevronRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
            </div>
          </Card>
        ))}
      </div>

      {/* Breakdown Modal */}
      {selectedDrive && (
        <DetailedScoreBreakdownModal
          isOpen={!!selectedDrive}
          onClose={() => setSelectedDrive(null)}
          title={selectedDrive.drive_title}
          subtitle={`Drive at ${selectedDrive.company_name || "Company"}`}
          score={selectedDrive.score}
          rawScore={selectedDrive.raw_score}
          tier={selectedDrive.tier}
          narrative={selectedDrive.overall_narrative}
          dimensionBreakdown={selectedDrive.dimension_breakdown}
          strengths={selectedDrive.strengths}
          gaps={selectedDrive.gaps}
          isEligible={selectedDrive.is_eligible}
          eligibilityReasons={selectedDrive.eligibility_reasons}
          detailedReportHref={`/student/placement/${selectedDrive.drive_id}`}
        />
      )}
    </>
  );
}
