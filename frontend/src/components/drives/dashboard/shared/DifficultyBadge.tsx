import React from "react";
import { DriveDifficultyLevel } from "@/types/drives";
import { Gauge } from "lucide-react";

interface DifficultyBadgeProps {
  level: DriveDifficultyLevel;
  className?: string;
}

const difficultyConfig: Record<DriveDifficultyLevel, { label: string; colors: string }> = {
  [DriveDifficultyLevel.beginner]: { label: "Beginner", colors: "bg-emerald-100 text-emerald-700 border-emerald-200" },
  [DriveDifficultyLevel.moderate]: { label: "Moderate", colors: "bg-blue-100 text-blue-700 border-blue-200" },
  [DriveDifficultyLevel.competitive]: { label: "Competitive", colors: "bg-indigo-100 text-indigo-700 border-indigo-200" },
  [DriveDifficultyLevel.highly_competitive]: { label: "Highly Competitive", colors: "bg-purple-100 text-purple-700 border-purple-200" },
  [DriveDifficultyLevel.elite]: { label: "Elite", colors: "bg-fuchsia-100 text-fuchsia-700 border-fuchsia-200" },
};

export default function DifficultyBadge({ level, className = "" }: DifficultyBadgeProps) {
  const config = difficultyConfig[level];

  if (!config) return null;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-semibold uppercase tracking-wider ${config.colors} ${className}`}>
      <Gauge className="h-3.5 w-3.5" />
      {config.label}
    </span>
  );
}
