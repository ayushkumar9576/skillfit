import React from "react";
import { DriveStatus } from "@/types/drives";
import { 
  CheckCircle2, 
  Loader2, 
  AlertCircle, 
  Send, 
  Archive, 
  FileEdit 
} from "lucide-react";

interface DriveStatusBadgeProps {
  status: DriveStatus;
}

export default function DriveStatusBadge({ status }: DriveStatusBadgeProps) {
  const getConfig = () => {
    switch (status) {
      case DriveStatus.draft:
        return {
          icon: <FileEdit className="h-4 w-4" aria-hidden="true" />,
          text: "Draft",
          colorClass: "bg-slate-100 text-slate-700 border-slate-200"
        };
      case DriveStatus.analyzing:
        return {
          icon: <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />,
          text: "Analyzing",
          colorClass: "bg-amber-100 text-amber-700 border-amber-200"
        };
      case DriveStatus.analysis_failed:
        return {
          icon: <AlertCircle className="h-4 w-4" aria-hidden="true" />,
          text: "Analysis Failed",
          colorClass: "bg-rose-100 text-rose-700 border-rose-200"
        };
      case DriveStatus.ready:
        return {
          icon: <CheckCircle2 className="h-4 w-4" aria-hidden="true" />,
          text: "Ready",
          colorClass: "bg-blue-100 text-blue-700 border-blue-200"
        };
      case DriveStatus.published:
        return {
          icon: <Send className="h-4 w-4" aria-hidden="true" />,
          text: "Published",
          colorClass: "bg-emerald-100 text-emerald-700 border-emerald-200"
        };
      case DriveStatus.archived:
        return {
          icon: <Archive className="h-4 w-4" aria-hidden="true" />,
          text: "Archived",
          colorClass: "bg-zinc-100 text-zinc-700 border-zinc-200"
        };
      default:
        return {
          icon: <FileEdit className="h-4 w-4" aria-hidden="true" />,
          text: "Unknown",
          colorClass: "bg-slate-100 text-slate-700 border-slate-200"
        };
    }
  };

  const config = getConfig();

  return (
    <div 
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md border text-sm font-medium ${config.colorClass}`}
      role="status"
      aria-label={`Drive status: ${config.text}`}
    >
      {config.icon}
      <span>{config.text}</span>
    </div>
  );
}
