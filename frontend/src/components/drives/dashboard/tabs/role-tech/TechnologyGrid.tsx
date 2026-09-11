import React, { useMemo } from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import TechnologyCategorySection from "./TechnologyCategorySection";
import { Code2 } from "lucide-react";
import { TechnologyIntelligence } from "@/types/drives";

const TECHNOLOGY_CATEGORY_ORDER = [
  "PROGRAMMING_LANGUAGE",
  "FRAMEWORK",
  "DATABASE",
  "CLOUD_PLATFORM",
  "DEVOPS_TOOL",
  "DATA_TECHNOLOGY",
  "TESTING_TECHNOLOGY",
  "OTHER",
];

export default function TechnologyGrid() {
  const { snapshot } = useDriveSnapshot();
  const technologies = snapshot?.intelligence_payload?.technologies;

  const groupedTechnologies = useMemo(() => {
    if (!technologies || technologies.length === 0) return null;

    const grouped = technologies.reduce((acc, tech) => {
      const cat = tech.category;
      if (!acc[cat]) {
        acc[cat] = [];
      }
      acc[cat].push(tech);
      return acc;
    }, {} as Record<string, TechnologyIntelligence[]>);

    // Sort deterministic
    const orderedGroups: { category: string; techs: TechnologyIntelligence[] }[] = [];
    
    // First, process known categories in order
    TECHNOLOGY_CATEGORY_ORDER.forEach((cat) => {
      if (grouped[cat]) {
        orderedGroups.push({ category: cat, techs: grouped[cat] });
        delete grouped[cat];
      }
    });

    // Process any remaining unknown categories
    Object.keys(grouped).sort().forEach((cat) => {
      orderedGroups.push({ category: cat, techs: grouped[cat] });
    });

    return orderedGroups;
  }, [technologies]);

  if (!groupedTechnologies) {
    return (
      <EmptyIntelligenceCard
        title="No Technologies Identified"
        description="The intelligence engine did not detect any specific technology requirements for this role."
        icon={Code2}
      />
    );
  }

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <Code2 className="h-4 w-4 text-indigo-500" />
        <h3 className="font-semibold text-slate-800">Technology Stack</h3>
      </div>
      
      <div className="p-5 flex flex-col gap-8">
        {groupedTechnologies.map((group, idx) => (
          <React.Fragment key={group.category}>
            <TechnologyCategorySection category={group.category} technologies={group.techs} />
            {idx < groupedTechnologies.length - 1 && <hr className="border-slate-100" />}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
