"use client";

import { useQuery } from "@tanstack/react-query";
import { getResumes, getCandidateProfile } from "@/lib/api/resume";
import Link from "next/link";
import { 
  UploadCloud, 
  Loader2, 
  AlertCircle, 
  FileText, 
  Clock, 
  CheckCircle2 
} from "lucide-react";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";
import Card from "@/components/shared/Card";
import StatusBadge from "@/components/shared/StatusBadge";
import ProgressTracker from "@/components/shared/ProgressTracker";

import ReadinessSummary from "@/components/analysis/ReadinessSummary";
import DomainIntelligenceOverview from "@/components/analysis/DomainIntelligenceOverview";
import EngineeringSignalsPanel from "@/components/analysis/EngineeringSignalsPanel";
import TechnologyMatrix from "@/components/analysis/TechnologyMatrix";
import CompetencyDashboard from "@/components/analysis/CompetencyDashboard";
import MissingEvidencePanel from "@/components/analysis/MissingEvidencePanel";
import PlacementRecommendations from "@/components/analysis/PlacementRecommendations";
import ImprovementRoadmap from "@/components/analysis/ImprovementRoadmap";
import EvidenceExplorer from "@/components/analysis/EvidenceExplorer";
import ProjectSophisticationPanel from "@/components/analysis/ProjectSophisticationPanel";

export default function AnalysisDashboardPage() {
  // 1. Fetch student resumes
  const { 
    data: resumesData, 
    isLoading: isLoadingResumes, 
    error: resumesError,
    refetch: refetchResumes 
  } = useQuery({
    queryKey: ["studentResumes"],
    queryFn: getResumes,
    refetchInterval: (query) => {
      const resumes = query.state.data?.resumes;
      const active = resumes?.find((r) => r.is_active) || resumes?.[0];
      // Only auto-poll if processing is actively underway
      if (active && active.processing_status === "processing") {
        return 4000;
      }
      return false;
    },
  });

  const activeResume = resumesData?.resumes?.find((r) => r.is_active) || resumesData?.resumes?.[0];
  const isCompleted = activeResume?.processing_status === "completed";
  const isProcessing = activeResume?.processing_status === "processing";
  const isUploaded = activeResume?.processing_status === "uploaded";
  const isFailed = activeResume?.processing_status === "failed";

  // 2. Fetch candidate intelligence profile ONLY when processing is completed
  const { 
    data: profile, 
    isLoading: isLoadingProfile, 
    error: profileError,
    refetch: refetchProfile 
  } = useQuery({
    queryKey: ["candidateProfile", activeResume?.id],
    queryFn: () => getCandidateProfile(activeResume!.id),
    enabled: !!activeResume && isCompleted,
    retry: 1,
  });

  // Loading state for initial resume check
  if (isLoadingResumes) {
    return <LoadingState message="Checking resume status..." />;
  }

  // Error fetching resumes list
  if (resumesError) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <ErrorState 
          message="Failed to load your resume records. Please try again." 
          retryAction={() => refetchResumes()}
        />
      </div>
    );
  }

  // State A: No resume uploaded yet
  if (!activeResume) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="bg-slate-100 p-6 rounded-full mb-6">
          <UploadCloud className="h-12 w-12 text-slate-400" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">No Resume Uploaded</h2>
        <p className="text-slate-500 max-w-md mx-auto mb-8 text-sm">
          Upload your resume to receive AI-powered placement intelligence and skill analysis.
        </p>
        <Link 
          href="/student/resume"
          className="inline-flex justify-center items-center rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors"
        >
          Upload Resume Now
        </Link>
      </div>
    );
  }

  // State B: Resume is Uploaded (Pending Administrator Review)
  if (isUploaded) {
    return (
      <div className="max-w-3xl mx-auto py-10 px-4 space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">CV Analysis</h1>
          <p className="text-sm text-slate-500 mt-1">Status of your resume analysis.</p>
        </div>

        <Card className="p-6 sm:p-8 space-y-6">
          <div className="flex items-start justify-between border-b border-slate-100 pb-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-amber-50 border border-amber-100 flex items-center justify-center shrink-0">
                <Clock className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900">Analysis Pending Review</h2>
                <p className="text-xs text-slate-500">Awaiting administrator review</p>
              </div>
            </div>
            <StatusBadge status="uploaded" />
          </div>

          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 flex items-center justify-between text-left">
            <div className="flex items-center gap-3 min-w-0">
              <FileText className="h-5 w-5 text-slate-500 shrink-0" />
              <div className="truncate">
                <p className="font-semibold text-sm text-slate-900 truncate">
                  {activeResume.file_name}
                </p>
                <p className="text-xs text-slate-500 capitalize">
                  {activeResume.resume_type} Resume • Uploaded {new Date(activeResume.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>

          <div className="py-2">
            <ProgressTracker status="uploaded" />
          </div>

          <div className="rounded-lg bg-blue-50/70 border border-blue-200/80 p-4 text-xs text-blue-800 leading-relaxed">
            Your resume has been uploaded successfully and is currently queued. Placement administrators review and initiate AI analysis. Once analyzed, your placement readiness score, verified skills matrix, and project insights will automatically be displayed here.
          </div>
        </Card>
      </div>
    );
  }

  // State C: Resume is currently Processing
  if (isProcessing) {
    return (
      <div className="max-w-3xl mx-auto py-10 px-4 space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">CV Analysis</h1>
          <p className="text-sm text-slate-500 mt-1">Status of your resume analysis.</p>
        </div>

        <Card className="p-6 sm:p-8 space-y-6">
          <div className="flex items-start justify-between border-b border-slate-100 pb-5">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
                <Loader2 className="h-5 w-5 text-indigo-600 animate-spin" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900">Analysis in Progress</h2>
                <p className="text-xs text-slate-500">Intelligence engine is evaluating your resume</p>
              </div>
            </div>
            <StatusBadge status="processing" />
          </div>

          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 flex items-center justify-between text-left">
            <div className="flex items-center gap-3 min-w-0">
              <FileText className="h-5 w-5 text-slate-500 shrink-0" />
              <div className="truncate">
                <p className="font-semibold text-sm text-slate-900 truncate">
                  {activeResume.file_name}
                </p>
                <p className="text-xs text-slate-500 capitalize">
                  {activeResume.resume_type} Resume • Uploaded {new Date(activeResume.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>

          <div className="py-2">
            <ProgressTracker status="processing" />
          </div>

          <div className="rounded-lg bg-indigo-50/70 border border-indigo-200/80 p-4 text-xs text-indigo-800 leading-relaxed">
            Your resume is currently being analyzed by the placement intelligence engine. This page will automatically refresh as soon as processing completes.
          </div>
        </Card>
      </div>
    );
  }

  // State D: Resume analysis Failed
  if (isFailed) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4">
        <Card className="p-8 text-center flex flex-col items-center border-red-200 bg-red-50/30">
          <div className="h-14 w-14 rounded-full bg-red-100 flex items-center justify-center mb-4">
            <AlertCircle className="h-7 w-7 text-red-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Analysis Could Not Be Completed</h2>
          <p className="text-slate-600 text-sm max-w-md mb-6 leading-relaxed">
            The automated intelligence engine was unable to extract or analyze structured content from &quot;{activeResume.file_name}&quot;. Please upload a fresh, clear PDF or DOCX file.
          </p>

          <Link
            href="/student/resume"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition-colors shadow-sm"
          >
            Upload New Resume
          </Link>
        </Card>
      </div>
    );
  }

  // State E: Completed, but failed to fetch profile snapshot
  if (profileError) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <ErrorState 
          message="Failed to load your analysis profile details. Please try refreshing." 
          retryAction={() => refetchProfile()}
        />
      </div>
    );
  }

  // State F: Completed, loading profile
  if (isLoadingProfile || !profile) {
    return <LoadingState message="Loading your placement intelligence profile..." />;
  }

  // State G: Completed & Loaded - Full Dashboard
  const readinessResult = {
    readiness_level: profile.findings?.some(f => f.severity === 'CRITICAL' || f.severity === 'HIGH') ? "NEEDS_IMPROVEMENT" : "READY",
    summary_text: profile.summary?.readiness_highlights?.join(" ") || "Profile analysis complete.",
    strength_areas: profile.findings?.filter(f => f.type === 'STRENGTH').map(f => f.title) || [],
    improvement_areas: profile.findings?.filter(f => f.type !== 'STRENGTH').map(f => f.title) || []
  };

  return (
    <div className="flex flex-col gap-8 max-w-full 2xl:max-w-[1920px] mx-auto pb-12 w-full">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Placement Intelligence Dashboard</h1>
            <p className="text-slate-500 max-w-3xl mt-1 text-sm">
              Evidence-first, evaluation-driven placement assessment generated from verifiable resume evidence.
            </p>
          </div>
          <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Verified Intelligence Snapshot
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8">
        <section>
          <ReadinessSummary 
            result={readinessResult} 
            isLoading={isLoadingProfile} 
          />
        </section>

        <section>
          <DomainIntelligenceOverview 
            domains={profile.domains} 
            isLoading={isLoadingProfile} 
          />
        </section>

        <section>
          <CompetencyDashboard 
            competencies={profile.competencies} 
            isLoading={isLoadingProfile} 
          />
        </section>

        <section>
          <TechnologyMatrix 
            technologies={profile.technologies} 
            isLoading={isLoadingProfile} 
          />
        </section>

        <section>
          <EngineeringSignalsPanel 
            engineeringSignals={profile.engineering_signals} 
            ownershipSignals={profile.ownership_signals} 
            isLoading={isLoadingProfile} 
          />
        </section>

        {profile.project_sophistication && profile.project_sophistication.length > 0 && (
          <section>
            <ProjectSophisticationPanel
              projectSophistication={profile.project_sophistication}
              averageProjectSophistication={profile.average_project_sophistication ?? 0}
              highestProjectSophistication={profile.highest_project_sophistication ?? 0}
              isLoading={isLoadingProfile}
            />
          </section>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <MissingEvidencePanel 
            findings={profile.findings} 
            isLoading={isLoadingProfile} 
          />
          <ImprovementRoadmap 
            recommendations={profile.recommendations} 
            isLoading={isLoadingProfile} 
          />
        </div>

        <section>
          <PlacementRecommendations 
            recommendations={profile.recommendations} 
            isLoading={isLoadingProfile} 
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
