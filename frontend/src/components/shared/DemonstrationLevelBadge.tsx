import React from "react";
import { DemonstrationLevel } from "@/types/candidate-profile";

interface DemonstrationLevelBadgeProps {
  level: DemonstrationLevel | string;
  className?: string;
}

export default function DemonstrationLevelBadge({ level, className = "" }: DemonstrationLevelBadgeProps) {
  const getStyle = () => {
    switch (level) {
      case DemonstrationLevel.ARCHITECTED:
      case DemonstrationLevel.DESIGNED:
        return "bg-purple-100 text-purple-800 ring-purple-600/20";
      case DemonstrationLevel.IMPLEMENTED:
        return "bg-emerald-100 text-emerald-800 ring-emerald-600/20";
      case DemonstrationLevel.USED:
        return "bg-blue-100 text-blue-800 ring-blue-600/20";
      case DemonstrationLevel.REFERENCED:
        return "bg-amber-100 text-amber-800 ring-amber-600/20";
      case DemonstrationLevel.CLAIMED:
      default:
        return "bg-slate-100 text-slate-800 ring-slate-600/10";
    }
  };

  const label = typeof level === "string" ? level.replace(/_/g, " ") : "UNKNOWN";

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${getStyle()} ${className}`}>
      {label}
    </span>
  );
}
