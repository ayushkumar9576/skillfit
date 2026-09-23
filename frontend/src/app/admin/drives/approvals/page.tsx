"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import DriveCard from "@/components/drives/DriveCard";
import { Loader2, Inbox } from "lucide-react";

export default function ApprovalsPage() {
  const [drives, setDrives] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadApprovals() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetchApi("/api/v1/drives?status=ready&limit=100");
        setDrives(response.drives || []);
      } catch (err: any) {
        setError("Failed to load awaiting approval queue. Please try again.");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }

    loadApprovals();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Awaiting Approval</h2>
          <p className="text-slate-500 mt-1">Review intelligence profiles and approve drives for publication.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
          <p className="text-slate-500">Loading approval queue...</p>
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
          <p className="text-slate-500 max-w-md">There are currently no drives awaiting approval.</p>
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
