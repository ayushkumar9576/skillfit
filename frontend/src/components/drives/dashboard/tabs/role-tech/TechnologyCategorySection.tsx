import React from "react";
import { TechnologyIntelligence } from "@/types/drives";
import TechnologyChip from "./TechnologyChip";

interface TechnologyCategorySectionProps {
  category: string;
  technologies: TechnologyIntelligence[];
}

export default function TechnologyCategorySection({ category, technologies }: TechnologyCategorySectionProps) {
  const formatCategoryName = (cat: string) => {
    return cat.replace(/_/g, " ").replace(/\w\S*/g, (txt) => {
      return txt.charAt(0).toUpperCase() + txt.substring(1).toLowerCase();
    });
  };

  return (
    <div className="flex flex-col gap-4">
      <h4 className="text-sm font-bold text-slate-700">{formatCategoryName(category)}</h4>
      <div className="flex flex-wrap gap-3">
        {technologies.map((tech, idx) => (
          <TechnologyChip key={`${tech.name}-${idx}`} technology={tech} />
        ))}
      </div>
    </div>
  );
}
