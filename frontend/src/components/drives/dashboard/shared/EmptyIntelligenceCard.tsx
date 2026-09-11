import React from "react";
import { LucideIcon } from "lucide-react";

interface EmptyIntelligenceCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

export default function EmptyIntelligenceCard({
  title,
  description,
  icon: Icon,
}: EmptyIntelligenceCardProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-slate-50/50 border border-slate-100 rounded-xl h-full w-full">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-slate-100 mb-4 text-slate-400">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-semibold text-slate-800 mb-1">{title}</h3>
      <p className="text-xs text-slate-500 max-w-sm">{description}</p>
    </div>
  );
}
