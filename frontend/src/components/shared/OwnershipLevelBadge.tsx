import React from "react";
import { OwnershipLevel } from "@/types/candidate-profile";

interface OwnershipLevelBadgeProps {
  level: OwnershipLevel | string;
  className?: string;
}

export default function OwnershipLevelBadge({ level, className = "" }: OwnershipLevelBadgeProps) {
  const getStyle = () => {
    switch (level) {
      case OwnershipLevel.LED:
        return "bg-purple-100 text-purple-800 ring-purple-600/20";
      case OwnershipLevel.OWNED:
        return "bg-emerald-100 text-emerald-800 ring-emerald-600/20";
      case OwnershipLevel.IMPLEMENTED:
        return "bg-blue-100 text-blue-800 ring-blue-600/20";
      case OwnershipLevel.CONTRIBUTED:
        return "bg-amber-100 text-amber-800 ring-amber-600/20";
      case OwnershipLevel.OBSERVED:
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
