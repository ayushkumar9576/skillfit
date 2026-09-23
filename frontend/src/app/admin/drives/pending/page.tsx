"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import DriveCard, { DriveStatusType } from "@/components/drives/DriveCard";
import { Loader2, Inbox } from "lucide-react";
import Link from "next/link";

export default function PendingAnalysisPage() {
  const [drives, setDrives] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPendingDrives() {
      setIsLoading(true);
      setError(null);
      try {
        // Fetch draft, analyzing, and analysis_failed concurrently
        const statuses: DriveStatusType[] = ["draft", "analyzing", "analysis_failed"];
        const promises = statuses.map((status) =>
          fetchApi(`/api/v1/drives?status=${status}&limit=100`)
        );

        const results = await Promise.all(promises);
        
        // Combine and sort by created_at descending
        const combinedDrives = results.flatMap(res => res.drives || []);
        combinedDrives.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        
        setDrives(combinedDrives);
      } catch (err: any) {
        setError("Failed to load pending drives. Please try again.");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }

    loadPendingDrives();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Pending Analysis</h2>
          <p className="text-slate-500 mt-1">Drives awaiting analysis, currently analyzing, or failed.</p>
        </div>
        <Link 
          href="/admin/drives/create"
          className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 transition-colors"
        >
          Create Drive
        </Link>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
          <p className="text-slate-500">Loading operational queue...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      ) : drives.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white border border-slate-200 rounded-xl shadow-sm text-center px-6">
          <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
            <Inbox className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">Queue is empty</h3>
          <p className="text-slate-500 max-w-md">There are currently no drives in the pending queue. Create a new drive to get started.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {drives.map((drive) => (
            <DriveCard key={drive.id} drive={drive} />
          ))}
        </div>
      )}
    </div>
  );
}
