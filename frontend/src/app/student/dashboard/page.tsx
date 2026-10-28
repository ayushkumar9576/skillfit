"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuthContext } from "@/providers/AuthProvider";
import { getStudentDashboard } from "@/lib/api/dashboard";
import { getResumes } from "@/lib/api/resume";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";
import Card from "@/components/shared/Card";
import StatusBadge from "@/components/shared/StatusBadge";
import ProgressTracker from "@/components/shared/ProgressTracker";
import { UploadCloud, FileText, UserCircle, Briefcase, Award, FolderGit2, Clock } from "lucide-react";
import Link from "next/link";

export default function StudentDashboardPage() {
  const { user } = useAuthContext();

  const { data: dashboardData, isLoading: isLoadingDash, error: dashError, refetch: refetchDash } = useQuery({
    queryKey: ["studentDashboard"],
    queryFn: getStudentDashboard,
  });

  const { data: resumesData, isLoading: isLoadingResumes, error: resumesError } = useQuery({
    queryKey: ["studentResumes"],
    queryFn: getResumes,
  });

  const isLoading = isLoadingDash || isLoadingResumes;

  if (isLoading) {
    return (
      <div className="p-8">
        <LoadingState message="Loading dashboard..." />
      </div>
    );
  }

  if (dashError || resumesError) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <ErrorState 
          message="Failed to load dashboard metrics. Please try again." 
          retryAction={() => refetchDash()}
        />
      </div>
    );
  }

  const latestResume = resumesData?.resumes?.[0];

  // The backend might return metrics in dashboardData. If none exist, we default.
  // Assuming dashboardData has { skills_count, projects_count, internships_count, certifications_count, readiness_level }
  const metrics = dashboardData || {};
  const isProfileComplete = user?.profile_completed;

  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      
      {/* Reminder Banner */}
      {!isProfileComplete && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <UserCircle className="h-6 w-6 text-amber-600" />
            <div>
              <h3 className="font-semibold text-amber-800">Complete Your Profile</h3>
              <p className="text-sm text-amber-700">Please complete your profile to unlock all features and better analysis.</p>
            </div>
          </div>
          <Link 
            href="/complete-profile" 
            className="px-4 py-2 bg-amber-600 text-white text-sm font-medium rounded-md hover:bg-amber-700 transition-colors"
          >
            Complete Now
          </Link>
        </div>
      )}

      {/* 1. Top Section */}
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Welcome back, {user?.full_name || "Student"}
          </h1>
          <p className="text-slate-500">
            {user?.registration_number} • {latestResume ? "Your resume is being tracked." : "Upload your first resume to begin analysis."}
          </p>
        </div>
        {latestResume && (
          <Card className="w-full lg:w-96 p-5 shrink-0 flex flex-col gap-4">
            <div className="flex justify-between items-center">
              <h3 className="font-semibold text-slate-700">Latest Resume</h3>
              <StatusBadge status={latestResume.processing_status} />
            </div>
            <ProgressTracker status={latestResume.processing_status} />
          </Card>
        )}
      </div>

      {/* Resume Processing / Pending Notice */}
      {latestResume && latestResume.processing_status !== "completed" && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
              <Clock className="h-5 w-5 text-indigo-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-800 text-sm">
                {latestResume.processing_status === "processing"
                  ? "Resume Analysis in Progress"
                  : latestResume.processing_status === "uploaded"
                  ? "Resume Analysis Pending Administrator Review"
                  : "Resume Analysis Failed"}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {latestResume.processing_status === "processing"
                  ? `"${latestResume.file_name}" is currently being evaluated by the intelligence engine.`
                  : latestResume.processing_status === "uploaded"
                  ? `"${latestResume.file_name}" has been uploaded and is awaiting administrator analysis.`
                  : `There was an issue processing "${latestResume.file_name}". Please upload a new CV.`}
              </p>
            </div>
          </div>
          <Link
            href="/student/analysis"
            className="self-start sm:self-auto px-3.5 py-1.5 bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-100 transition-colors shrink-0 shadow-sm"
          >
            Check Status
          </Link>
        </div>
      )}

      {/* 2. Second Section: Metrics */}
      <div>
        <h2 className="text-xl font-bold text-slate-800 mb-4">Your Overview</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          <Card className="p-5 flex flex-col gap-2 border-indigo-100 bg-indigo-50/30">
            <div className="flex items-center gap-2 text-indigo-600">
              <UserCircle className="h-5 w-5" />
              <span className="font-semibold text-sm">Profile</span>
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {isProfileComplete ? "100%" : "Pending"}
            </div>
            <p className="text-xs text-slate-500">{isProfileComplete ? "Fully complete" : "Action required"}</p>
          </Card>

          <Card className="p-5 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-slate-600">
              <Award className="h-5 w-5" />
              <span className="font-semibold text-sm">Readiness</span>
            </div>
            <div className="text-xl font-bold text-slate-900 mt-1">
              {metrics.readiness_level ? (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider
                  ${metrics.readiness_level === 'HIGH' ? 'bg-emerald-100 text-emerald-800' : 
                    metrics.readiness_level === 'MEDIUM' ? 'bg-amber-100 text-amber-800' : 
                    'bg-red-100 text-red-800'}`
                }>
                  {metrics.readiness_level}
                </span>
              ) : (
                <span className="text-slate-400 text-base">Not Available</span>
              )}
            </div>
          </Card>

          <Card className="p-5 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-slate-600">
              <FileText className="h-5 w-5" />
              <span className="font-semibold text-sm">Skills</span>
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {metrics.skills_count || 0}
            </div>
          </Card>

          <Card className="p-5 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-slate-600">
              <FolderGit2 className="h-5 w-5" />
              <span className="font-semibold text-sm">Projects</span>
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {metrics.projects_count || 0}
            </div>
          </Card>

          <Card className="p-5 flex flex-col gap-2">
            <div className="flex items-center gap-2 text-slate-600">
              <Briefcase className="h-5 w-5" />
              <span className="font-semibold text-sm">Internships</span>
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {metrics.internships_count || 0}
            </div>
          </Card>
        </div>
      </div>

      {/* 3. Third Section: Quick Actions */}
      <div>
        <h2 className="text-xl font-bold text-slate-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link href="/student/resume" className="group">
            <Card className="p-5 hover:border-indigo-300 hover:shadow-md transition-all h-full flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-indigo-50 flex items-center justify-center group-hover:bg-indigo-100 transition-colors">
                <UploadCloud className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Upload Resume</h3>
                <p className="text-xs text-slate-500">Update your stored CV</p>
              </div>
            </Card>
          </Link>
          
          <Link href="/student/analysis" className="group">
            <Card className="p-5 hover:border-indigo-300 hover:shadow-md transition-all h-full flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-indigo-50 flex items-center justify-center group-hover:bg-indigo-100 transition-colors">
                <FileText className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">View Analysis</h3>
                <p className="text-xs text-slate-500">
                  {latestResume?.processing_status === "completed" 
                    ? "See your latest insights" 
                    : latestResume?.processing_status === "processing" 
                    ? "Analysis in progress..." 
                    : latestResume 
                    ? "Analysis pending review" 
                    : "Upload CV to begin"}
                </p>
              </div>
            </Card>
          </Link>

          <Link href="/student/placement" className="group">
            <Card className="p-5 hover:border-indigo-300 hover:shadow-md transition-all h-full flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-emerald-50 flex items-center justify-center group-hover:bg-emerald-100 transition-colors">
                <Briefcase className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Placement Drives</h3>
                <p className="text-xs text-slate-500">Matched opportunities</p>
              </div>
            </Card>
          </Link>

          <Link href="/student/profile" className="group">
            <Card className="p-5 hover:border-indigo-300 hover:shadow-md transition-all h-full flex items-center gap-4">
              <div className="h-10 w-10 rounded-full bg-indigo-50 flex items-center justify-center group-hover:bg-indigo-100 transition-colors">
                <UserCircle className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Update Profile</h3>
                <p className="text-xs text-slate-500">Edit your details</p>
              </div>
            </Card>
          </Link>
        </div>
      </div>

      {/* 5. Mentor Section (Coming Soon) */}
      <div className="pt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-800">Mentorship</h2>
          <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">
            Coming Soon
          </span>
        </div>
        <Card className="p-8 border-dashed border-slate-200 bg-slate-50 flex flex-col items-center text-center justify-center">
          <h3 className="text-slate-500 font-medium mb-1">Mentor matching is under development</h3>
          <p className="text-sm text-slate-400">Soon you&apos;ll be able to connect with industry experts based on your skill gaps.</p>
        </Card>
      </div>

    </div>
  );
}
