import React from "react";
import TargetArchetypeCard from "./TargetArchetypeCard";
import DifficultySelectivityCard from "./DifficultySelectivityCard";
import RiskAlertsCard from "./RiskAlertsCard";
import CompensationSummaryCard from "./CompensationSummaryCard";

export default function ExecutiveSummaryHero() {
  return (
    <section 
      className="w-full mb-8" 
      aria-label="Executive Summary"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 items-stretch">
        <TargetArchetypeCard />
        <DifficultySelectivityCard />
        <RiskAlertsCard />
        <CompensationSummaryCard />
      </div>
    </section>
  );
}
