import React from "react";
import { ImportanceLevel } from "@/types/drives";

interface SeverityPillProps {
  level: ImportanceLevel; // Risk severity uses ImportanceLevel enum
  className?: string;
}

const severityConfig: Record<ImportanceLevel, { label: string; colors: string }> = {
  [ImportanceLevel.critical]: { label: "Critical Risk", colors: "bg-rose-100 text-rose-700 border-rose-200" },
  [ImportanceLevel.high]: { label: "High Risk", colors: "bg-orange-100 text-orange-700 border-orange-200" },
  [ImportanceLevel.medium]: { label: "Moderate Risk", colors: "bg-amber-100 text-amber-700 border-amber-200" },
  [ImportanceLevel.low]: { label: "Low Risk", colors: "bg-slate-50 text-slate-600 border-slate-200" },
};

export default function SeverityPill({ level, className = "" }: SeverityPillProps) {
  const config = severityConfig[level];

  if (!config) return null;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${config.colors} ${className}`}>
      {config.label}
    </span>
  );
}
