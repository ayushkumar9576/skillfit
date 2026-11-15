"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { ArrowLeft, Building2, FileText } from "lucide-react";
import IntelligenceReview from "@/components/drives/IntelligenceReview";
import ErrorState from "@/components/shared/ErrorState";
import LoadingState from "@/components/shared/LoadingState";
import { getDrive } from "@/services/drives/driveService";
import { getLatestSnapshot } from "@/services/drives/snapshotService";
import { parseApiError } from "@/lib/utils";

export default function StudentDriveReportPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ["studentDriveReport", id],
    queryFn: async () => {
      const [drive, snapshot] = await Promise.all([getDrive(id), getLatestSnapshot(id)]);
      return { drive, snapshot };
    },
    // Recheck publication status whenever the report is opened.
    staleTime: 0,
    gcTime: 0,
    retry: false,
    refetchOnWindowFocus: true,
  });

  const unavailable = axios.isAxiosError(error) && error.response?.status === 404;

  return (
    <div className="space-y-6 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      <Link
        href="/student/placement"
        className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-800"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to Placement Drives
      </Link>

      <div className="space-y-2">
        <h1 className="flex items-center gap-3 text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
          <FileText className="h-7 w-7 text-indigo-600 shrink-0" aria-hidden="true" />
          Drive Analysis Report
        </h1>
        {!error && data && (
          <p className="flex items-center gap-2 text-sm text-slate-600">
            <Building2 className="h-4 w-4 shrink-0" aria-hidden="true" />
            {data.drive.company_name} · {data.drive.role}
          </p>
        )}
      </div>

      {isPending ? (
        <LoadingState message="Loading drive analysis report..." />
      ) : error ? (
        <ErrorState
          title={unavailable ? "Report unavailable" : "Unable to load report"}
          message={unavailable
            ? "This drive is no longer published or its analysis report is not available yet."
            : parseApiError(error).message}
          retryAction={() => refetch()}
        />
      ) : data ? (
        <IntelligenceReview snapshot={data.snapshot} />
      ) : null}
    </div>
  );
}
