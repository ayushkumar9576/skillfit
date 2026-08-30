"use client";

import { useQuery } from "@tanstack/react-query";
import { getResumes, getCandidateProfile } from "@/lib/api/resume";
import Link from "next/link";
import { UploadCloud } from "lucide-react";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";

import ReadinessSummary from "@/components/analysis/ReadinessSummary";
import DomainIntelligenceOverview from "@/components/analysis/DomainIntelligenceOverview";
import EngineeringSignalsPanel from "@/components/analysis/EngineeringSignalsPanel";
import TechnologyMatrix from "@/components/analysis/TechnologyMatrix";
import CompetencyDashboard from "@/components/analysis/CompetencyDashboard";
import MissingEvidencePanel from "@/components/analysis/MissingEvidencePanel";
import PlacementRecommendations from "@/components/analysis/PlacementRecommendations";
import ImprovementRoadmap from "@/components/analysis/ImprovementRoadmap";
import EvidenceExplorer from "@/components/analysis/EvidenceExplorer";

export default function AnalysisDashboardPage() {
  const { data: resumesData, isLoading: isLoadingResumes, error: resumesError } = useQuery({
    queryKey: ["studentResumes"],
    queryFn: getResumes,
  });

  const activeResume = resumesData?.resumes?.find((r) => r.is_active) || resumesData?.resumes?.[0];

  const { data: profile, isLoading: isLoadingProfile, error: profileError } = useQuery({
    queryKey: ["candidateProfile", activeResume?.id],
    queryFn: () => getCandidateProfile(activeResume!.id),
    enabled: !!activeResume,
  });

  const isLoading = isLoadingResumes || isLoadingProfile;
  const error = resumesError || profileError;

  if (isLoading) {
    return <LoadingState message="Loading your intelligence profile..." />;
  }

  if (error) {
    return <ErrorState message="Failed to load your analysis dashboard." />;
  }

  if (!activeResume || !profile) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <div className="bg-slate-100 p-6 rounded-full mb-6">
          <UploadCloud className="h-12 w-12 text-slate-400" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">No Analysis Available</h2>
        <p className="text-slate-500 max-w-md mx-auto mb-8">
          Upload your resume to generate a comprehensive placement intelligence profile. We&apos;ll analyze your projects, skills, and experience to match you with the right roles.
        </p>
        <Link 
          href="/student/resume"
          className="inline-flex justify-center items-center rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700"
        >
          Upload Resume
        </Link>
      </div>
    );
  }

  // Derive readiness result dynamically from the profile
  const readinessResult = {
    readiness_level: profile.findings?.some(f => f.severity === 'CRITICAL' || f.severity === 'HIGH') ? "NEEDS_IMPROVEMENT" : "READY",
    summary_text: profile.summary?.readiness_highlights?.join(" ") || "Profile analysis complete.",
    strength_areas: profile.findings?.filter(f => f.type === 'STRENGTH').map(f => f.title) || [],
    improvement_areas: profile.findings?.filter(f => f.type !== 'STRENGTH').map(f => f.title) || []
  };

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto pb-12">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Placement Intelligence Dashboard</h1>
        <p className="text-slate-500 max-w-3xl">
          An evidence-first, evaluation-driven project intelligence system that produces hiring-relevant assessments from verifiable resume evidence.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        <section>
          <ReadinessSummary 
            result={readinessResult} 
            isLoading={isLoading} 
          />
        </section>

        <section>
          <DomainIntelligenceOverview 
            domains={profile.domains} 
            isLoading={isLoading} 
          />
        </section>

        <section>
          <CompetencyDashboard 
            competencies={profile.competencies} 
            isLoading={isLoading} 
          />
        </section>

        <section>
          <TechnologyMatrix 
            technologies={profile.technologies} 
            isLoading={isLoading} 
          />
        </section>

        <section>
          <EngineeringSignalsPanel 
            engineeringSignals={profile.engineering_signals} 
            ownershipSignals={profile.ownership_signals} 
            isLoading={isLoading} 
          />
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <MissingEvidencePanel 
            findings={profile.findings} 
            isLoading={isLoading} 
          />
          <ImprovementRoadmap 
            recommendations={profile.recommendations} 
            isLoading={isLoading} 
          />
        </div>

        <section>
          <PlacementRecommendations 
            recommendations={profile.recommendations} 
            isLoading={isLoading} 
          />
        </section>
        
        {profile.technologies && profile.technologies.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Evidence Explorer (Sample)</h3>
            <EvidenceExplorer 
              title={profile.technologies[0].technology} 
              evidence={profile.technologies[0].evidence || []} 
              level={profile.technologies[0].demonstration_level} 
            />
          </section>
        )}
      </div>
    </div>
  );
}
