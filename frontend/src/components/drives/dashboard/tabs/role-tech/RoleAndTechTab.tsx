import React from "react";
import DomainIdentityCard from "./DomainIdentityCard";
import TechnologySummaryBanner from "./TechnologySummaryBanner";
import TechnologyGrid from "./TechnologyGrid";
import TechnicalCompetencySection from "./TechnicalCompetencySection";
import BehavioralCompetencySection from "./BehavioralCompetencySection";
import RoleExpectationsCard from "./RoleExpectationsCard";

export default function RoleAndTechTab() {
  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      <TechnologySummaryBanner />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <DomainIdentityCard />
        </div>
        <div className="lg:col-span-2">
          <RoleExpectationsCard />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <TechnologyGrid />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TechnicalCompetencySection />
        <BehavioralCompetencySection />
      </div>
      
    </div>
  );
}
