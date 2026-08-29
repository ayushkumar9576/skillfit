import React from "react";
import { FolderGit2, Briefcase, Award, UserCircle, HelpCircle } from "lucide-react";
import { IntelligenceSourceType } from "@/types/candidate-profile";

interface EvidenceSourceBadgeProps {
  source: IntelligenceSourceType | string;
  className?: string;
}

export default function EvidenceSourceBadge({ source, className = "" }: EvidenceSourceBadgeProps) {
  const getStyleAndIcon = () => {
    switch (source) {
      case IntelligenceSourceType.PROJECT:
        return {
          style: "bg-indigo-50 text-indigo-700 ring-indigo-600/20",
          icon: <FolderGit2 className="h-3.5 w-3.5 mr-1" />
        };
      case IntelligenceSourceType.INTERNSHIP:
        return {
          style: "bg-blue-50 text-blue-700 ring-blue-600/20",
          icon: <Briefcase className="h-3.5 w-3.5 mr-1" />
        };
      case IntelligenceSourceType.CERTIFICATION:
        return {
          style: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
          icon: <Award className="h-3.5 w-3.5 mr-1" />
        };
      case IntelligenceSourceType.SELF_REPORTED:
        return {
          style: "bg-amber-50 text-amber-700 ring-amber-600/20",
          icon: <UserCircle className="h-3.5 w-3.5 mr-1" />
        };
      default:
        return {
          style: "bg-slate-50 text-slate-700 ring-slate-600/20",
          icon: <HelpCircle className="h-3.5 w-3.5 mr-1" />
        };
    }
  };

  const { style, icon } = getStyleAndIcon();
  const label = typeof source === "string" ? source.replace(/_/g, " ") : "UNKNOWN";

  return (
    <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${style} ${className}`}>
      {icon}
      {label}
    </span>
  );
}
