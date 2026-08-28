"use client";

import { useState } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import { 
  getResumes, 
  getResumeReadiness,
  getResumeSkills,
  getResumeProjects,
  getResumeInternships,
  getResumeCertifications
} from "@/lib/api/resume";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";
import EmptyState from "@/components/shared/EmptyState";
import Card from "@/components/shared/Card";
import { UploadCloud, Clock, CheckCircle2, TrendingUp, Code2, Briefcase, Award, Zap, AlertCircle } from "lucide-react";
import Link from "next/link";

export default function StudentAnalysisPage() {
  const { data: resumesData, isLoading: isLoadingResumes, error: resumesError, refetch } = useQuery({
    queryKey: ["studentResumes"],
    queryFn: getResumes,
  });

  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);

  // Documented Architecture Rule:
  // The backend explicitly guarantees `created_at DESC` ordering in GET /api/v1/resumes.
  // Therefore, index 0 is deterministically the most recently uploaded resume.
  const activeResume = resumesData?.resumes?.find(r => r.id === selectedResumeId) || resumesData?.resumes?.[0];
  const isCompleted = activeResume?.processing_status === "completed";

  const results = useQueries({
    queries: [
      { queryKey: ["readiness", activeResume?.id], queryFn: () => getResumeReadiness(activeResume!.id), enabled: isCompleted },
      { queryKey: ["skills", activeResume?.id], queryFn: () => getResumeSkills(activeResume!.id), enabled: isCompleted },
      { queryKey: ["projects", activeResume?.id], queryFn: () => getResumeProjects(activeResume!.id), enabled: isCompleted },
      { queryKey: ["internships", activeResume?.id], queryFn: () => getResumeInternships(activeResume!.id), enabled: isCompleted },
      { queryKey: ["certifications", activeResume?.id], queryFn: () => getResumeCertifications(activeResume!.id), enabled: isCompleted },
    ]
  });

  if (isLoadingResumes) {
    return <LoadingState message="Loading your latest resume status..." className="mt-20" />;
  }

  if (resumesError) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <ErrorState message="Could not fetch resume status." retryAction={() => refetch()} />
      </div>
    );
  }

  if (!activeResume) {
    return (
      <div className="p-8 max-w-4xl mx-auto mt-10">
        <EmptyState 
          icon={UploadCloud}
          title="No Resume Uploaded" 
          description="Upload your first resume to begin AI-powered analysis and placement intelligence."
          action={
            <Link href="/student/resume" className="rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors">
              Upload Resume
            </Link>
          }
        />
      </div>
    );
  }

  if (!isCompleted) {
    return (
      <div className="p-8 max-w-4xl mx-auto mt-10">
        <EmptyState 
          icon={Clock}
          title="Analysis Pending" 
          description={`Your resume (${activeResume.file_name}) is currently in the queue. Waiting for administrator review and processing.`}
        />
      </div>
    );
  }

  const isAnalyzing = results.some(q => q.isLoading);
  const isError = results.some(q => q.isError);

  if (isAnalyzing) {
    return <LoadingState message="Fetching your personalized analysis results..." className="mt-20" />;
  }

  if (isError) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <ErrorState message="Failed to load some analysis components." retryAction={() => results.forEach(q => q.refetch())} />
      </div>
    );
  }

  const [readinessData, skillsData, projectsData, internshipsData, certificationsData] = results.map(q => q.data);

  return (
    <div className="space-y-10 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Resume Analysis</h1>
          <p className="text-sm text-slate-500 mt-1">Based on your resume: <span className="font-semibold text-slate-700">{activeResume.file_name}</span></p>
        </div>

        {resumesData?.resumes && resumesData.resumes.length > 1 && (
          <div className="flex items-center gap-3">
            <label htmlFor="resume-selector" className="text-sm font-medium text-slate-700 shrink-0">Select Resume:</label>
            <select
              id="resume-selector"
              value={activeResume.id}
              onChange={(e) => setSelectedResumeId(e.target.value)}
              className="block w-full sm:w-auto rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer shadow-sm"
            >
              {resumesData.resumes.map((resume) => (
                <option key={resume.id} value={resume.id}>
                  {resume.resume_type.charAt(0).toUpperCase() + resume.resume_type.slice(1)} Resume
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="space-y-12">
        {/* 1. Readiness Assessment */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-indigo-100 p-2 rounded-lg"><TrendingUp className="h-5 w-5 text-indigo-600" /></div>
            <h2 className="text-2xl font-bold text-slate-800">Readiness Assessment</h2>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <Card className="p-6 md:p-8 flex flex-col items-center justify-center bg-slate-50 border-slate-100">
              <span className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Readiness Level</span>
              <span className={`text-4xl font-extrabold ${
                readinessData?.readiness_level === 'HIGH' ? 'text-emerald-600' : 
                readinessData?.readiness_level === 'MEDIUM' ? 'text-amber-500' : 
                'text-red-500'
              }`}>
                {readinessData?.readiness_level || "UNKNOWN"}
              </span>
            </Card>
            
            <Card className="p-6 md:p-8 col-span-1 lg:col-span-2">
              <h3 className="text-lg font-bold text-slate-800 mb-3">Analysis Summary</h3>
              <p className="text-slate-600 leading-relaxed text-sm md:text-base">
                {readinessData?.summary?.split('\n')[0] || "No summary available."}
              </p>
              <p className="text-slate-600 leading-relaxed text-sm md:text-base mt-2">
                {readinessData?.readiness_explanation || ""}
              </p>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-500" /> Key Strengths
              </h3>
              {readinessData?.strengths?.items?.length > 0 ? (
                <ul className="space-y-4">
                  {readinessData.strengths.items.map((strength: {title: string; description: string;}, idx: number) => (
                    <li key={idx} className="flex flex-col gap-1">
                      <span className="text-sm font-semibold text-slate-900">{strength.title}</span>
                      <span className="text-sm text-slate-600">{strength.description}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500 italic">No notable strengths identified.</p>
              )}
            </Card>
            
            <Card className="p-6">
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-amber-500" /> Critical Gaps
              </h3>
              {readinessData?.weaknesses?.items?.length > 0 ? (
                <ul className="space-y-4">
                  {readinessData.weaknesses.items.map((gap: {title: string; description: string;}, idx: number) => (
                    <li key={idx} className="flex flex-col gap-1">
                      <span className="text-sm font-semibold text-slate-900">{gap.title}</span>
                      <span className="text-sm text-slate-600">{gap.description}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500 italic">No notable gaps identified.</p>
              )}
            </Card>
          </div>
        </section>

        {/* 2. Skills Analysis */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-indigo-100 p-2 rounded-lg"><Zap className="h-5 w-5 text-indigo-600" /></div>
            <h2 className="text-2xl font-bold text-slate-800">Skills Analysis</h2>
          </div>
          {skillsData?.skills?.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {skillsData.skills.map((skill: { name: string; hiring_signal: string; evidence_count: number; }, idx: number) => (
                <Card key={idx} className="p-5 flex flex-col justify-between">
                  <div>
                    <h3 className="font-bold text-slate-800 text-lg mb-1">{skill.name}</h3>
                    <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">
                      Hiring Signal: 
                      <span className={`ml-1 ${skill.hiring_signal === 'high' ? 'text-emerald-600' : skill.hiring_signal === 'medium' ? 'text-amber-500' : 'text-slate-400'}`}>
                        {skill.hiring_signal}
                      </span>
                    </p>
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span>Evidence Count: {skill.evidence_count || 0}</span>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center text-slate-500">No skills detected.</Card>
          )}
        </section>

        {/* 3. Projects Analysis */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-indigo-100 p-2 rounded-lg"><Code2 className="h-5 w-5 text-indigo-600" /></div>
            <h2 className="text-2xl font-bold text-slate-800">Projects Analysis</h2>
          </div>
          {projectsData?.projects?.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {projectsData.projects.map((proj: { title: string; technologies?: string[]; description: string; }, idx: number) => (
                <Card key={idx} className="p-6">
                  <h3 className="font-bold text-slate-900 text-lg">{proj.title}</h3>
                  {proj.technologies && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {proj.technologies.map((tech: string, i: number) => (
                        <span key={i} className="px-2.5 py-1 bg-slate-100 text-slate-600 rounded-md text-xs font-medium">
                          {tech}
                        </span>
                      ))}
                    </div>
                  )}
                  <p className="text-sm text-slate-600 mt-4 leading-relaxed">{proj.description}</p>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center text-slate-500">No projects detected.</Card>
          )}
        </section>

        {/* 4. Internship Analysis */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-indigo-100 p-2 rounded-lg"><Briefcase className="h-5 w-5 text-indigo-600" /></div>
            <h2 className="text-2xl font-bold text-slate-800">Internship Analysis</h2>
          </div>
          {internshipsData?.internships?.length > 0 ? (
            <div className="space-y-4">
              {internshipsData.internships.map((intern: { role: string; company: string; description: string; }, idx: number) => (
                <Card key={idx} className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-3">
                    <h3 className="font-bold text-slate-900 text-lg">{intern.role}</h3>
                    <span className="text-sm font-semibold text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full w-fit">
                      {intern.company}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 leading-relaxed">{intern.description}</p>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center text-slate-500">No internships detected.</Card>
          )}
        </section>

        {/* 5. Certification Analysis */}
        <section>
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-indigo-100 p-2 rounded-lg"><Award className="h-5 w-5 text-indigo-600" /></div>
            <h2 className="text-2xl font-bold text-slate-800">Certification Analysis</h2>
          </div>
          {certificationsData?.certifications?.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {certificationsData.certifications.map((cert: { name: string; issuer: string; }, idx: number) => (
                <Card key={idx} className="p-5 flex items-start gap-4">
                  <CheckCircle2 className="h-6 w-6 text-emerald-500 shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-bold text-slate-900">{cert.name}</h3>
                    <p className="text-sm text-slate-500 mt-1">{cert.issuer}</p>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center text-slate-500">No certifications detected.</Card>
          )}
        </section>

      </div>
    </div>
  );
}
