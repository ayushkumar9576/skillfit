import React from "react";
import { DriveStatus } from "@/types/drives";

interface StatusBadgeProps {
  status: DriveStatus;
  className?: string;
}

const statusConfig: Record<DriveStatus, { label: string; colors: string }> = {
  [DriveStatus.draft]: { label: "Draft", colors: "bg-slate-100 text-slate-700" },
  [DriveStatus.analyzing]: { label: "Analyzing", colors: "bg-amber-100 text-amber-700 animate-pulse" },
  [DriveStatus.analysis_failed]: { label: "Analysis Failed", colors: "bg-rose-100 text-rose-700" },
  [DriveStatus.ready]: { label: "Ready", colors: "bg-blue-100 text-blue-700" },
  [DriveStatus.published]: { label: "Published", colors: "bg-emerald-100 text-emerald-700" },
  [DriveStatus.archived]: { label: "Archived", colors: "bg-zinc-100 text-zinc-700" },
};

export default function StatusBadge({ status, className = "" }: StatusBadgeProps) {
  const config = statusConfig[status];
  
  if (!config) return null;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.colors} ${className}`}>
      {config.label}
    </span>
  );
}
