"use client";

import { useQuery } from "@tanstack/react-query";
import { getAdminDashboard } from "@/lib/api/admin";
import PageHeader from "@/components/shared/PageHeader";
import MetricCard from "@/components/shared/MetricCard";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";
import { Users, GraduationCap, UploadCloud, Clock, CheckCircle2, XCircle } from "lucide-react";

export default function AdminDashboardPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["adminDashboard"],
    queryFn: getAdminDashboard,
  });

  if (isLoading) {
    return <LoadingState message="Loading dashboard metrics..." className="mt-20" />;
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <ErrorState message="Failed to load dashboard data." retryAction={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <PageHeader 
        title="Admin Dashboard" 
        description="System overview and platform metrics."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <MetricCard 
          title="Total Students" 
          value={data.total_students} 
          icon={<GraduationCap className="h-5 w-5" />}
        />
        <MetricCard 
          title="Total Faculty" 
          value={data.total_faculty} 
          icon={<Users className="h-5 w-5" />}
        />
      </div>

      <div>
        <h2 className="text-xl font-bold text-slate-900 mb-4 mt-8">Resume Queue Overview</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard 
            title="Uploaded" 
            value={data.uploaded_resumes} 
            icon={<UploadCloud className="h-5 w-5 text-slate-500" />}
          />
          <MetricCard 
            title="Processing" 
            value={data.processing_resumes} 
            icon={<Clock className="h-5 w-5 text-amber-500" />}
          />
          <MetricCard 
            title="Completed" 
            value={data.completed_resumes} 
            icon={<CheckCircle2 className="h-5 w-5 text-emerald-500" />}
          />
          <MetricCard 
            title="Failed" 
            value={data.failed_resumes} 
            icon={<XCircle className="h-5 w-5 text-red-500" />}
          />
        </div>
      </div>
    </div>
  );
}
