"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import { DriveStatusType } from "@/components/drives/DriveCard";
import IntelligenceReview from "@/components/drives/IntelligenceReview";
import { 
  Building2, 
  Briefcase, 
  MapPin, 
  IndianRupee, 
  FileText, 
  Calendar,
  Loader2,
  AlertCircle,
  Play,
  RotateCcw,
  CheckCircle,
  Clock,
  Globe,
  XCircle
} from "lucide-react";
import { format } from "date-fns";

export default function DriveWorkspacePage() {
  const { id } = useParams() as { id: string };
  const router = useRouter();
  
  const [drive, setDrive] = useState<any>(null);
  const [snapshot, setSnapshot] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isActioning, setIsActioning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const driveData = await fetchApi(`/api/v1/drives/${id}`);
      setDrive(driveData);

      // If it's ready or published, try to fetch the snapshot
      if (driveData.status === "ready" || driveData.status === "published") {
        try {
          const snapshotData = await fetchApi(`/api/v1/drives/${id}/snapshots/latest`);
          setSnapshot(snapshotData);
        } catch (snapErr) {
          console.error("Failed to load snapshot:", snapErr);
          // Don't fail the whole page if snapshot is missing, just log it
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to load drive workspace.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  // Poll for status updates if the drive is currently analyzing
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (drive?.status === "analyzing") {
      interval = setInterval(async () => {
        try {
          const driveData = await fetchApi(`/api/v1/drives/${id}`);
          if (driveData.status !== "analyzing") {
            // Status changed! Reload full data to get snapshot or failure state
            loadData();
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 5000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [drive?.status, id]);

  const handleStartAnalysis = async () => {
    setIsActioning(true);
    try {
      await fetchApi(`/api/v1/drives/${id}/analyze`, { method: "POST" });
      await loadData(); // Reload to get new status
    } catch (err: any) {
      alert(`Analysis failed to start: ${err.message}`);
    } finally {
      setIsActioning(false);
    }
  };

  const handleCancelAnalysis = async () => {
    setIsActioning(true);
    try {
      await fetchApi(`/api/v1/drives/${id}/cancel-analysis`, { method: "POST" });
      await loadData();
    } catch (err: any) {
      alert(`Failed to cancel analysis: ${err.message}`);
    } finally {
      setIsActioning(false);
    }
  };

  const handleApprovePublish = async () => {
    setIsActioning(true);
    try {
      await fetchApi(`/api/v1/drives/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "published" })
      });
      router.push("/admin/drives/published");
    } catch (err: any) {
      alert(`Publish failed: ${err.message}`);
      setIsActioning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-32">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mb-4" />
        <p className="text-slate-500">Loading drive workspace...</p>
      </div>
    );
  }

  if (error || !drive) {
    return (
      <div className="bg-red-50 p-6 rounded-xl border border-red-100 flex flex-col items-center text-center">
        <AlertCircle className="w-10 h-10 text-red-500 mb-3" />
        <h3 className="text-lg font-semibold text-red-800">Error Loading Drive</h3>
        <p className="text-red-600 mt-1">{error || "Drive not found"}</p>
        <button onClick={() => router.push("/admin/drives")} className="mt-4 px-4 py-2 bg-red-100 text-red-800 rounded-lg hover:bg-red-200 transition-colors">
          Return to Workspace Home
        </button>
      </div>
    );
  }

  const status: DriveStatusType = drive.status;

  const renderActionArea = () => {
    switch (status) {
      case "draft":
        return (
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Analysis Pending</h3>
              <p className="text-sm text-slate-500 mt-1">This drive is currently in draft state. Start the intelligence analysis to extract skills and competencies.</p>
            </div>
            <button
              onClick={handleStartAnalysis}
              disabled={isActioning}
              className="flex-shrink-0 flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              {isActioning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
              Start Analysis
            </button>
          </div>
        );
      case "analyzing":
        return (
          <div className="space-y-4">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                  <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" />
                  Analysis in Progress
                </h3>
                <p className="text-sm text-slate-500 mt-1">Our intelligence engine is currently analyzing the drive context. This may take a few moments.</p>
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={handleCancelAnalysis}
                disabled={isActioning}
                className="text-sm font-medium text-red-500 hover:text-red-700 transition-colors flex items-center gap-2 px-3 py-1.5 rounded hover:bg-red-50"
              >
                {isActioning ? <Loader2 className="w-3 h-3 animate-spin" /> : <XCircle className="w-3 h-3" />}
                Cancel Analysis
              </button>
              <button
                onClick={handleStartAnalysis}
                disabled={isActioning}
                className="text-sm font-medium text-slate-500 hover:text-indigo-600 transition-colors flex items-center gap-2 px-3 py-1.5 rounded hover:bg-slate-50"
              >
                {isActioning ? <Loader2 className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3" />}
                Force Restart
              </button>
            </div>
          </div>
        );
      case "analysis_failed":
        return (
          <div className="bg-red-50 p-6 rounded-xl border border-red-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-red-900">Analysis Failed</h3>
              <p className="text-sm text-red-700 mt-1">The intelligence engine encountered an error while processing this drive context.</p>
            </div>
            <button
              onClick={handleStartAnalysis}
              disabled={isActioning}
              className="flex-shrink-0 flex items-center gap-2 px-5 py-2.5 bg-red-100 text-red-800 font-medium rounded-lg hover:bg-red-200 border border-red-300 transition-colors disabled:opacity-50"
            >
              {isActioning ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />}
              Retry Analysis
            </button>
          </div>
        );
      case "ready":
        return (
          <div className="space-y-6">
            <div className="bg-emerald-50 p-6 rounded-xl border border-emerald-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-emerald-900 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5" /> Analysis Complete
                </h3>
                <p className="text-sm text-emerald-800 mt-1">The intelligence profile is ready for review. Approve and publish to make this drive live.</p>
              </div>
              <button
                onClick={handleApprovePublish}
                disabled={isActioning}
                className="flex-shrink-0 flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
              >
                {isActioning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
                Approve & Publish
              </button>
            </div>
            
            {snapshot ? (
              <IntelligenceReview snapshot={snapshot} />
            ) : (
              <div className="p-4 bg-amber-50 text-amber-800 border border-amber-200 rounded-lg">
                Warning: Snapshot could not be loaded for review.
              </div>
            )}
          </div>
        );
      case "published":
        return (
          <div className="space-y-6">
            <div className="bg-slate-50 p-6 rounded-xl border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Globe className="w-5 h-5 text-emerald-600" /> Published Drive
              </h3>
              <p className="text-sm text-slate-500 mt-1">This drive is live and visible to students.</p>
            </div>
            {snapshot && <IntelligenceReview snapshot={snapshot} />}
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="bg-white p-6 md:p-8 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0 border border-indigo-100">
            <Building2 className="w-8 h-8 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{drive.company_name}</h1>
            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500 mt-2">
              <div className="flex items-center gap-1.5 font-medium text-slate-700 bg-slate-100 px-2.5 py-1 rounded-md">
                <Briefcase className="w-4 h-4" />
                {drive.role}
              </div>
              <div className="flex items-center gap-1.5">
                <Clock className="w-4 h-4" />
                Created {format(new Date(drive.created_at), "MMM d, yyyy")}
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center px-4 py-2 bg-slate-100 text-slate-700 font-semibold rounded-lg border border-slate-200 uppercase tracking-wider text-sm">
          Status: {status}
        </div>
      </div>

      {/* Action Area (Lifecycle dependent) */}
      {renderActionArea()}

      {/* Metadata Section */}
      <div className="bg-white p-6 md:p-8 rounded-xl border border-slate-200 shadow-sm space-y-6">
        <h2 className="text-xl font-bold text-slate-900 border-b border-slate-100 pb-4">Drive Metadata</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div>
              <h4 className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1.5">
                <IndianRupee className="w-4 h-4" /> Package
              </h4>
              <p className="text-slate-900 font-medium">{drive.package || "Not specified"}</p>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1.5">
                <MapPin className="w-4 h-4" /> Location
              </h4>
              <p className="text-slate-900 font-medium">{drive.location || "Not specified"}</p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1.5">
                <Calendar className="w-4 h-4" /> Application Deadline
              </h4>
              <p className="text-slate-900 font-medium">
                {drive.application_deadline ? format(new Date(drive.application_deadline), "MMM d, yyyy") : "Not specified"}
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <h4 className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-1.5">
                <FileText className="w-4 h-4" /> Eligibility Criteria
              </h4>
              <p className="text-slate-900">{drive.eligibility_criteria || "Not specified"}</p>
            </div>
          </div>
        </div>
        
        {drive.description && (
          <div className="pt-6 border-t border-slate-100">
            <h4 className="text-sm font-medium text-slate-500 flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4" /> Description
            </h4>
            <div className="text-slate-700 whitespace-pre-wrap">{drive.description}</div>
          </div>
        )}
      </div>
    </div>
  );
}
