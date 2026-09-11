"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useDrive } from "@/hooks/drives/useDrives";
import { useLatestSnapshot } from "@/hooks/drives/useSnapshots";
import { useAnalysisHistory, useTriggerAnalysis } from "@/hooks/drives/useAnalysis";
import { SnapshotProvider } from "./context/SnapshotProvider";
import DashboardLoadingState from "./states/DashboardLoadingState";
import DashboardErrorState from "./states/DashboardErrorState";
import DashboardEmptyState from "./states/DashboardEmptyState";
import DashboardAnalyzingState from "./states/DashboardAnalyzingState";
import DashboardFailedState from "./states/DashboardFailedState";
import { DASHBOARD_TABS } from "./tabs/dashboardTabs";
import DriveHeader from "./header/DriveHeader";
import ExecutiveSummaryHero from "./hero/ExecutiveSummaryHero";
import RoleAndTechTab from "./tabs/role-tech/RoleAndTechTab";
import EligibilityAndTermsTab from "./tabs/eligibility/EligibilityAndTermsTab";
import SelectionAndPreparationTab from "./tabs/selection-preparation/SelectionAndPreparationTab";
import { EvidenceProvider } from "./shared/evidence/EvidenceContext";
import EvidenceModal from "./shared/evidence/EvidenceModal";
import SnapshotHistoryDrawer from "./history/SnapshotHistoryDrawer";
import { History } from "lucide-react";
import dynamic from "next/dynamic";

import TabLoadingSkeleton from "./states/TabLoadingSkeleton";

const EvaluationTab = dynamic(() => import("./tabs/evaluation/EvaluationTab"), {
  loading: () => <TabLoadingSkeleton />
});
const AuditTab = dynamic(() => import("./tabs/audit/AuditTab"), {
  loading: () => <TabLoadingSkeleton />
});

interface DriveDashboardContainerProps {
  driveId: string;
}

export default function DriveDashboardContainer({ driveId }: DriveDashboardContainerProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // URL Tab State
  const tabParam = searchParams.get("tab");
  const defaultTab = DASHBOARD_TABS[0].id;
  const [activeTab, setActiveTab] = useState(tabParam || defaultTab);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Sync state to URL if it changes without triggering full navigation initially
  useEffect(() => {
    if (tabParam && tabParam !== activeTab) {
      setActiveTab(tabParam);
    } else if (!tabParam) {
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.set("tab", activeTab);
      window.history.replaceState({}, "", newUrl.toString());
    }
  }, [tabParam, activeTab]);

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    const newUrl = new URL(window.location.href);
    newUrl.searchParams.set("tab", tabId);
    router.replace(newUrl.toString(), { scroll: false });
  };

  // Queries (Parallel)
  const { data: drive, isLoading: isLoadingDrive, error: driveError, refetch: refetchDrive } = useDrive(driveId);
  const { data: latestSnapshot, isLoading: isLoadingSnapshot, error: snapshotError } = useLatestSnapshot(driveId);
  const { data: analysisHistory, isLoading: isLoadingAnalysis } = useAnalysisHistory(driveId, drive);
  
  const { mutate: triggerAnalysis, isPending: isTriggering } = useTriggerAnalysis(driveId);

  // Derived States
  const isLoading = isLoadingDrive || (isLoadingSnapshot && drive?.status === "ready"); // Snapshot is optional if not ready
  const hasSnapshot = !!latestSnapshot;
  
  const latestAnalysis = analysisHistory?.analyses?.[0];
  const isAnalyzing = drive?.status === "analyzing" || latestAnalysis?.status === "pending" || latestAnalysis?.status === "running";
  const isFailed = drive?.status === "analysis_failed" || latestAnalysis?.status === "failed";
  const isDraft = drive?.status === "draft";

  // State Machine Render Logic
  if (isLoading) {
    return <DashboardLoadingState />;
  }

  if (driveError) {
    return <DashboardErrorState message={driveError.message} onRetry={refetchDrive} />;
  }

  if (isAnalyzing) {
    return <DashboardAnalyzingState />;
  }

  if (isFailed) {
    return (
      <DashboardFailedState 
        errorMessage={latestAnalysis?.error_message} 
        onRetry={() => triggerAnalysis()} 
        isRetrying={isTriggering} 
      />
    );
  }

  if (!hasSnapshot && isDraft) {
    return (
      <DashboardEmptyState 
        onRunAnalysis={() => triggerAnalysis()} 
        isTriggering={isTriggering} 
      />
    );
  }

  // If no snapshot and not draft, something unexpected occurred
  if (!hasSnapshot && !isDraft && !isAnalyzing && !isFailed) {
      return (
          <DashboardEmptyState 
            onRunAnalysis={() => triggerAnalysis()} 
            isTriggering={isTriggering} 
          />
      );
  }

  // Main UI Render (Foundation only, no polishing)
  return (
    <SnapshotProvider snapshot={latestSnapshot || null} driveId={driveId}>
      <EvidenceProvider>
        <div className="max-w-7xl mx-auto space-y-6 relative">
          {drive && <DriveHeader drive={drive} />}

        <div className="px-4 sm:px-6 lg:px-8">
          <ExecutiveSummaryHero />
        </div>

        {/* Tab Navigation Architecture */}
        <div className="border-b border-slate-200 bg-white sticky top-0 z-10 flex items-center justify-between">
          <nav 
            className="flex space-x-2 md:space-x-8 px-4 overflow-x-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]" 
            aria-label="Drive Intelligence Tabs"
            role="tablist"
          >
            {DASHBOARD_TABS.map((tab, index) => {
              const isActive = activeTab === tab.id;
              
              const handleKeyDown = (e: React.KeyboardEvent) => {
                if (e.key === 'ArrowRight') {
                  const nextTab = DASHBOARD_TABS[(index + 1) % DASHBOARD_TABS.length];
                  handleTabChange(nextTab.id);
                  document.getElementById(`tab-${nextTab.id}`)?.focus();
                } else if (e.key === 'ArrowLeft') {
                  const prevTab = DASHBOARD_TABS[(index - 1 + DASHBOARD_TABS.length) % DASHBOARD_TABS.length];
                  handleTabChange(prevTab.id);
                  document.getElementById(`tab-${prevTab.id}`)?.focus();
                } else if (e.key === 'Home') {
                  handleTabChange(DASHBOARD_TABS[0].id);
                  document.getElementById(`tab-${DASHBOARD_TABS[0].id}`)?.focus();
                } else if (e.key === 'End') {
                  handleTabChange(DASHBOARD_TABS[DASHBOARD_TABS.length - 1].id);
                  document.getElementById(`tab-${DASHBOARD_TABS[DASHBOARD_TABS.length - 1].id}`)?.focus();
                }
              };

              return (
                <button
                  key={tab.id}
                  id={`tab-${tab.id}`}
                  role="tab"
                  aria-selected={isActive}
                  aria-controls={`tabpanel-${tab.id}`}
                  tabIndex={isActive ? 0 : -1}
                  onClick={() => handleTabChange(tab.id)}
                  onKeyDown={handleKeyDown}
                  className={`
                    whitespace-nowrap py-4 px-2 border-b-2 font-medium text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2
                    ${isActive 
                      ? 'border-indigo-500 text-indigo-600' 
                      : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                    }
                  `}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>
          
          <div className="ml-auto flex items-center pr-4">
            <button
              onClick={() => setIsHistoryOpen(true)}
              className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-indigo-600 bg-slate-100 hover:bg-indigo-50 px-3 py-1.5 rounded-md transition-colors"
            >
              <History className="h-4 w-4" />
              Snapshot History
            </button>
          </div>
        </div>

        {/* Tab Content Architecture */}
        <div className="py-6" role="tabpanel" id={`tabpanel-${activeTab}`} aria-labelledby={`tab-${activeTab}`} tabIndex={0}>
          {activeTab === "role-tech" && <RoleAndTechTab />}
          {activeTab === "eligibility" && <EligibilityAndTermsTab />}
          {activeTab === "selection" && <SelectionAndPreparationTab />}
          {activeTab === "evaluation" && <EvaluationTab />}
          {activeTab === "audit" && <AuditTab driveId={driveId} />}
          
          {(!["role-tech", "eligibility", "selection", "evaluation", "audit"].includes(activeTab)) && (
            <div className="border border-slate-200 border-dashed rounded-lg p-12 bg-slate-50 flex items-center justify-center">
              <p className="text-sm text-slate-500 font-mono">
                [Content for Tab: {activeTab} Placeholder]
              </p>
            </div>
          )}
        </div>

        {/* Global Modals & Drawers */}
        <EvidenceModal />
        <SnapshotHistoryDrawer 
          driveId={driveId} 
          drive={drive} 
          isOpen={isHistoryOpen} 
          onClose={() => setIsHistoryOpen(false)} 
        />
        
      </div>
      </EvidenceProvider>
    </SnapshotProvider>
  );
}
