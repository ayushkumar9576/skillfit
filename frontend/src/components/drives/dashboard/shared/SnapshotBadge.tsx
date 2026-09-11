import React from "react";
import { Clock } from "lucide-react";

interface SnapshotBadgeProps {
  version: string;
  isLatest?: boolean;
  className?: string;
}

export default function SnapshotBadge({ version, isLatest = false, className = "" }: SnapshotBadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border ${
      isLatest 
        ? "bg-indigo-50 text-indigo-700 border-indigo-200" 
        : "bg-slate-50 text-slate-600 border-slate-200"
    } ${className}`}>
      <Clock className="h-3 w-3" />
      Snapshot {version}
      {isLatest && <span className="ml-1 text-indigo-500 font-bold">(Latest)</span>}
    </span>
  );
}
