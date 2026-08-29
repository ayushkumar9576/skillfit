"use client";

import { useState, useEffect } from "react";
import ReadinessSummary from "@/components/analysis/ReadinessSummary";
import DomainIntelligenceOverview from "@/components/analysis/DomainIntelligenceOverview";
import EngineeringSignalsPanel from "@/components/analysis/EngineeringSignalsPanel";
import TechnologyMatrix from "@/components/analysis/TechnologyMatrix";
import CompetencyDashboard from "@/components/analysis/CompetencyDashboard";
import MissingEvidencePanel from "@/components/analysis/MissingEvidencePanel";
import PlacementRecommendations from "@/components/analysis/PlacementRecommendations";
import ImprovementRoadmap from "@/components/analysis/ImprovementRoadmap";
import EvidenceExplorer from "@/components/analysis/EvidenceExplorer";
import { mockCandidateProfile as profile, mockReadinessResult } from "@/mocks/candidate-profile";

export default function AnalysisDashboardPage() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate data loading
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto pb-12">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Placement Intelligence Dashboard</h1>
        <p className="text-slate-500 max-w-3xl">
          An evidence-first, evaluation-driven project intelligence system that produces hiring-relevant assessments from verifiable resume evidence.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        <section>
          <ReadinessSummary 
            result={mockReadinessResult} 
            isLoading={isLoading} 
          />
        </section>

        <section>
          <DomainIntelligenceOverview 
            domains={profile.domains} 
            isLoading={isLoading} 
          />
        </section>

        <section>
          <CompetencyDashboard 
            competencies={profile.competencies} 
            isLoading={isLoading} 
          />
        </section>

        <section>
          <TechnologyMatrix 
            technologies={profile.technologies} 
            isLoading={isLoading} 
          />
        </section>

        <section>
          <EngineeringSignalsPanel 
            engineeringSignals={profile.engineering_signals} 
            ownershipSignals={profile.ownership_signals} 
            isLoading={isLoading} 
          />
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <MissingEvidencePanel 
            findings={profile.findings} 
            isLoading={isLoading} 
          />
          <ImprovementRoadmap 
            recommendations={profile.recommendations} 
            isLoading={isLoading} 
          />
        </div>

        <section>
          <PlacementRecommendations 
            recommendations={profile.recommendations} 
            isLoading={isLoading} 
          />
        </section>
        
        <section>
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Evidence Explorer (Sample)</h3>
          <EvidenceExplorer 
            title="Python" 
            evidence={profile.technologies[0]?.evidence || []} 
            level={profile.technologies[0]?.demonstration_level} 
          />
        </section>
      </div>
    </div>
  );
}
