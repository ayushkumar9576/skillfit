"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRecommendedCandidates, RecommendedCandidate } from "@/lib/api/matching";
import Card from "@/components/shared/Card";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";
import DetailedScoreBreakdownModal from "@/components/dashboard/DetailedScoreBreakdownModal";
import { CheckCircle2, XCircle, User, ChevronRight, BarChart3 } from "lucide-react";

interface Props {
  driveId: string;
}

export default function RecommendedCandidates({ driveId }: Props) {
  const [selectedCandidate, setSelectedCandidate] = useState<RecommendedCandidate | null>(null);

  const { data: candidates, isLoading, error } = useQuery({
    queryKey: ["recommendedCandidates", driveId],
    queryFn: () => getRecommendedCandidates(driveId),
    enabled: !!driveId,
  });

  if (isLoading) {
    return <LoadingState message="Loading recommended candidates..." />;
  }

  if (error) {
    return <ErrorState message="Failed to load candidates." />;
  }

  if (!candidates || candidates.length === 0) {
    return (
      <Card className="p-8 text-center text-slate-500">
        No matching candidates available at the moment.
      </Card>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        {candidates.map((candidate: RecommendedCandidate) => (
          <Card 
            key={candidate.candidate_id} 
            className="p-5 flex flex-col justify-between gap-4 hover:border-indigo-400 hover:shadow-md transition-all cursor-pointer group"
            onClick={() => setSelectedCandidate(candidate)}
          >
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg text-slate-900 flex items-center gap-2 group-hover:text-indigo-600 transition-colors">
                    <User className="w-5 h-5 text-indigo-500 shrink-0" />
                    {candidate.student_name}
                  </h3>
                </div>
                <div className="text-right">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide ${
                    candidate.tier === "EXCELLENT_MATCH" ? "bg-emerald-100 text-emerald-800" :
                    candidate.tier === "STRONG_MATCH" ? "bg-indigo-100 text-indigo-800" :
                    candidate.tier === "MODERATE_MATCH" ? "bg-amber-100 text-amber-800" :
                    "bg-red-100 text-red-800"
                  }`}>
                    {candidate.tier.replace("_MATCH", "")}
                  </span>
                  <div className="mt-2 text-xl font-bold text-slate-700">
                    {Math.round(candidate.score * 100)}% Match
                  </div>
                </div>
              </div>

              <div className="text-sm text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100/80">
                {candidate.overall_narrative}
              </div>

              <div className="grid grid-cols-2 gap-4 mt-2">
                <div>
                  <h4 className="text-xs font-semibold text-emerald-700 uppercase mb-2">Top Strengths</h4>
                  <ul className="space-y-1">
                    {candidate.strengths.length > 0 ? candidate.strengths.map((str, idx) => (
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
                    {candidate.gaps.length > 0 ? candidate.gaps.map((gap, idx) => (
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
      {selectedCandidate && (
        <DetailedScoreBreakdownModal
          isOpen={!!selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
          title={selectedCandidate.student_name}
          subtitle="Candidate Alignment with Drive Requirements"
          score={selectedCandidate.score}
          rawScore={selectedCandidate.raw_score}
          tier={selectedCandidate.tier}
          narrative={selectedCandidate.overall_narrative}
          dimensionBreakdown={selectedCandidate.dimension_breakdown}
          strengths={selectedCandidate.strengths}
          gaps={selectedCandidate.gaps}
        />
      )}
    </>
  );
}
