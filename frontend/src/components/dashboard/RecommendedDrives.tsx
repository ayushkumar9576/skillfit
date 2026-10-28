"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRecommendedDrives, RecommendedDrive } from "@/lib/api/matching";
import Card from "@/components/shared/Card";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";
import DetailedScoreBreakdownModal from "@/components/dashboard/DetailedScoreBreakdownModal";
import { Building2, CheckCircle2, XCircle, ChevronRight, BarChart3 } from "lucide-react";

export default function RecommendedDrives() {
  const [selectedDrive, setSelectedDrive] = useState<RecommendedDrive | null>(null);

  const { data: drives, isLoading, error } = useQuery({
    queryKey: ["recommendedDrives"],
    queryFn: () => getRecommendedDrives(),
  });

  if (isLoading) {
    return <LoadingState message="Loading recommended drives..." />;
  }

  if (error) {
    return <ErrorState message="Failed to load recommendations." />;
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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {drives.map((drive: RecommendedDrive) => (
          <Card 
            key={drive.drive_id} 
            className="p-5 flex flex-col justify-between gap-4 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer group"
            onClick={() => setSelectedDrive(drive)}
          >
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg text-slate-900 group-hover:text-indigo-600 transition-colors">
                    {drive.drive_title}
                  </h3>
                  <div className="flex items-center text-slate-500 text-sm mt-1">
                    <Building2 className="w-4 h-4 mr-1.5 text-slate-400 shrink-0" />
                    <span className="font-medium">{drive.company_name || "Unknown Company"}</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide ${
                    drive.tier === "EXCELLENT_MATCH" ? "bg-emerald-100 text-emerald-800" :
                    drive.tier === "STRONG_MATCH" ? "bg-indigo-100 text-indigo-800" :
                    drive.tier === "MODERATE_MATCH" ? "bg-amber-100 text-amber-800" :
                    "bg-red-100 text-red-800"
                  }`}>
                    {drive.tier.replace("_MATCH", "")}
                  </span>
                  <div className="mt-2 text-xl font-bold text-slate-700">
                    {Math.round(drive.score * 100)}% Match
                  </div>
                </div>
              </div>

              <div className="text-sm text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100/80">
                {drive.overall_narrative}
              </div>

              <div className="grid grid-cols-2 gap-4 mt-2">
                <div>
                  <h4 className="text-xs font-semibold text-emerald-700 uppercase mb-2">Top Strengths</h4>
                  <ul className="space-y-1">
                    {drive.strengths.length > 0 ? drive.strengths.map((str, idx) => (
                      <li key={idx} className="flex items-start text-xs text-slate-700 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mr-1.5 shrink-0 mt-0.5" />
                        <span className="line-clamp-1">{str}</span>
                      </li>
                    )) : <li className="text-xs text-slate-400">None</li>}
                  </ul>
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-rose-700 uppercase mb-2">Key Gaps</h4>
                  <ul className="space-y-1">
                    {drive.gaps.length > 0 ? drive.gaps.map((gap, idx) => (
                      <li key={idx} className="flex items-start text-xs text-slate-700 font-medium">
                        <XCircle className="w-3.5 h-3.5 text-rose-500 mr-1.5 shrink-0 mt-0.5" />
                        <span className="line-clamp-1">{gap}</span>
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
                View Detailed Score Breakdown
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
        />
      )}
    </>
  );
}
