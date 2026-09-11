import React from "react";
import HiringSignalsSection from "./HiringSignalsSection";
import SuccessIndicatorsGrid from "./SuccessIndicatorsGrid";
import RiskBreakdownSection from "./RiskBreakdownSection";
import DifficultyBreakdownCard from "./DifficultyBreakdownCard";

export default function EvaluationTab() {
  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <HiringSignalsSection />
        <SuccessIndicatorsGrid />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskBreakdownSection />
        <DifficultyBreakdownCard />
      </div>
      
    </div>
  );
}
