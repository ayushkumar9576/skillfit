import React from "react";
import { ImportanceLevel } from "@/types/drives";

interface ImportancePillProps {
  level: ImportanceLevel;
  className?: string;
}

const importanceConfig: Record<ImportanceLevel, { label: string; colors: string }> = {
  [ImportanceLevel.critical]: { label: "Critical", colors: "bg-indigo-100 text-indigo-700 border-indigo-200" },
  [ImportanceLevel.high]: { label: "High", colors: "bg-purple-100 text-purple-700 border-purple-200" },
  [ImportanceLevel.medium]: { label: "Medium", colors: "bg-blue-50 text-blue-700 border-blue-200" },
  [ImportanceLevel.low]: { label: "Low", colors: "bg-slate-50 text-slate-600 border-slate-200" },
};

export default function ImportancePill({ level, className = "" }: ImportancePillProps) {
  const config = importanceConfig[level];

  if (!config) return null;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${config.colors} ${className}`}>
      {config.label}
    </span>
  );
}
