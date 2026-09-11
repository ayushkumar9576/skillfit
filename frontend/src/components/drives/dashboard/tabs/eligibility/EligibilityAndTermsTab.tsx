import React from "react";
import QualificationGateMatrix from "./QualificationGateMatrix";
import ExperienceRequirementsCard from "./ExperienceRequirementsCard";
import ServiceAgreementCard from "./ServiceAgreementCard";
import WorkArrangementCard from "./WorkArrangementCard";
import ShiftIntelligenceCard from "./ShiftIntelligenceCard";

export default function EligibilityAndTermsTab() {
  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <QualificationGateMatrix />
        </div>
        <div className="lg:col-span-1 flex flex-col gap-6">
          <ExperienceRequirementsCard />
          <ServiceAgreementCard />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <WorkArrangementCard />
        <ShiftIntelligenceCard />
      </div>
      
    </div>
  );
}
