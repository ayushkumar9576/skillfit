"use client";

import React, { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import DriveCard from "@/components/drives/DriveCard";
import { Loader2, Globe } from "lucide-react";

export default function PublishedDrivesPage() {
  const [drives, setDrives] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPublished() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetchApi("/api/v1/drives?status=published&limit=100");
        setDrives(response.drives || []);
      } catch (err: any) {
        setError("Failed to load published drives. Please try again.");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }

    loadPublished();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Published Drives</h2>
          <p className="text-slate-500 mt-1">Live drives currently visible and available to students.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
          <p className="text-slate-500">Loading published drives...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
          {error}
        </div>
      ) : drives.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white border border-slate-200 rounded-xl shadow-sm text-center px-6">
          <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mb-4">
            <Globe className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">No published drives</h3>
          <p className="text-slate-500 max-w-md">There are currently no live drives. Approve drives in the awaiting approval queue to publish them.</p>
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
