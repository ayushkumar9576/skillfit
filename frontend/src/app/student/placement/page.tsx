"use client";

import RecommendedDrives from "@/components/dashboard/RecommendedDrives";
import Card from "@/components/shared/Card";
import { Building2, Sparkles, FileText, CheckCircle2 } from "lucide-react";
import Link from "next/link";

export default function StudentPlacementDrivesPage() {
  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      {/* 1. Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center">
              <Building2 className="h-5 w-5 text-indigo-600" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">
              Placement Drives
            </h1>
          </div>
          <p className="text-slate-500 text-sm">
            Explore verified placement opportunities with AI-driven match intelligence tailored to your CV profile.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            AI Matching Active
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-indigo-600" />
            Approved Drives Only
          </span>
        </div>
      </div>

      {/* 2. Intelligence Matching Insight Banner */}
      <Card className="p-4 sm:p-5 bg-gradient-to-r from-indigo-50/50 via-slate-50 to-white border-indigo-100/70 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            How Drive Recommendations Work
          </h3>
          <p className="text-xs text-slate-600 max-w-2xl">
            Match scores and alignment tiers are computed deterministically across technologies, competencies, and project sophistication between your verified CV intelligence and approved placement drives.
          </p>
        </div>
        <Link
          href="/student/resume"
          className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-indigo-700 bg-white border border-indigo-200 rounded-md hover:bg-indigo-50 transition-colors shrink-0 shadow-sm"
        >
          <FileText className="w-3.5 h-3.5 text-indigo-600" />
          Update Stored CV
        </Link>
      </Card>

      {/* 3. Recommended Drives Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-800">Available Drives &amp; Matches</h2>
        </div>
        <RecommendedDrives />
      </div>
    </div>
  );
}
