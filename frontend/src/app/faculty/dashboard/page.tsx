"use client";

import { useQuery } from "@tanstack/react-query";
import { getFacultyDashboard } from "@/lib/api/faculty";
import PageHeader from "@/components/shared/PageHeader";
import MetricCard from "@/components/shared/MetricCard";
import LoadingState from "@/components/shared/LoadingState";
import ErrorState from "@/components/shared/ErrorState";
import { BookOpen, Users } from "lucide-react";
import Card from "@/components/shared/Card";

export default function FacultyDashboardPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["facultyDashboard"],
    queryFn: getFacultyDashboard,
  });

  if (isLoading) {
    return <LoadingState message="Loading dashboard..." className="mt-20" />;
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <ErrorState message="Failed to load dashboard data." retryAction={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <PageHeader 
        title="Faculty Dashboard" 
        description="Welcome to your faculty portal."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MetricCard 
          title="Department" 
          value={data.department || "Not Set"} 
          subtitle={data.profile_completed ? "Profile Completed" : "Profile Incomplete"}
          icon={<BookOpen className="h-5 w-5" />}
        />
        
        <Card className="p-6 flex flex-col justify-center items-center text-center bg-slate-50 border border-slate-200 border-dashed rounded-2xl shadow-sm min-h-[160px]">
          <div className="p-3 bg-indigo-100 text-indigo-600 rounded-full mb-3">
            <Users className="h-6 w-6" />
          </div>
          <h3 className="font-bold text-slate-900">Mentorship Features</h3>
          <p className="text-sm text-slate-500 mt-1">Student tracking and mentoring features are coming soon.</p>
        </Card>
      </div>
    </div>
  );
}
