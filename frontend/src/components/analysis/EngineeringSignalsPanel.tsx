import { Server, Shield, Activity, Share2, Component, CheckSquare, Layers } from "lucide-react";
import StateWrapper from "./StateWrapper";
import { EngineeringSignal, OwnershipIntelligence, EngineeringSignalCategory } from "@/types/candidate-profile";
import EvidenceSourceBadge from "@/components/shared/EvidenceSourceBadge";
import OwnershipLevelBadge from "@/components/shared/OwnershipLevelBadge";

interface EngineeringSignalsPanelProps {
  engineeringSignals: EngineeringSignal[];
  ownershipSignals: OwnershipIntelligence[];
  isLoading?: boolean;
  error?: Error | null;
}

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  [EngineeringSignalCategory.ARCHITECTURE]: <Layers className="h-4 w-4 text-purple-500" />,
  [EngineeringSignalCategory.DEPLOYMENT]: <Server className="h-4 w-4 text-blue-500" />,
  [EngineeringSignalCategory.SECURITY]: <Shield className="h-4 w-4 text-red-500" />,
  [EngineeringSignalCategory.MONITORING]: <Activity className="h-4 w-4 text-emerald-500" />,
  [EngineeringSignalCategory.INTEGRATION]: <Share2 className="h-4 w-4 text-orange-500" />,
  [EngineeringSignalCategory.TESTING]: <CheckSquare className="h-4 w-4 text-indigo-500" />,
};

export default function EngineeringSignalsPanel({
  engineeringSignals,
  ownershipSignals,
  isLoading = false,
  error = null,
}: EngineeringSignalsPanelProps) {
  const hasSignals = (engineeringSignals && engineeringSignals.length > 0) || (ownershipSignals && ownershipSignals.length > 0);

  // Group engineering signals by category
  const groupedSignals = (engineeringSignals || []).reduce((acc, signal) => {
    const cat = signal.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(signal);
    return acc;
  }, {} as Record<string, EngineeringSignal[]>);

  return (
    <StateWrapper
      isLoading={isLoading}
      error={error}
      isEmpty={!hasSignals}
      emptyTitle="No Engineering Signals Detected"
      emptyMessage="No evidence of engineering best practices or project ownership was found."
    >
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Component className="h-5 w-5 text-indigo-500" />
            Engineering & Ownership Signals
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            Demonstrated engineering maturity and project ownership levels.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Engineering Signals Section */}
          <div className="space-y-6">
            <h4 className="font-semibold text-slate-800 border-b border-slate-200 pb-2">
              Engineering Practices
            </h4>
            
            <div className="space-y-4">
              {Object.entries(groupedSignals).length > 0 ? Object.entries(groupedSignals).map(([category, signals]) => (
                <div key={category} className="rounded-lg border border-slate-100 bg-slate-50/50 p-4">
                  <h5 className="flex items-center gap-2 font-medium text-slate-700 mb-3 capitalize">
                    {CATEGORY_ICONS[category] || <Component className="h-4 w-4 text-slate-500" />}
                    {category.toLowerCase()}
                  </h5>
                  <ul className="space-y-3">
                    {signals.map((sig, idx) => (
                      <li key={idx} className="flex flex-col gap-1.5 border-l-2 border-indigo-200 pl-3 ml-1">
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-sm font-medium text-slate-900">{sig.signal}</span>
                          <span className={`shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                            sig.demonstrated ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
                          }`}>
                            {sig.demonstrated ? "DEMONSTRATED" : "NOT DEMONSTRATED"}
                          </span>
                        </div>
                        
                        <div className="flex flex-wrap gap-2 text-xs text-slate-500 items-center">
                          <span className="font-medium">Evidence: {sig.evidence?.length || 0}</span>
                          {sig.evidence && sig.evidence.length > 0 && (
                            <>
                              <span className="text-slate-300">•</span>
                              <div className="flex flex-wrap gap-1">
                                {Array.from(new Set(sig.evidence.map(e => e.source))).map(src => (
                                  <EvidenceSourceBadge key={src} source={src} />
                                ))}
                              </div>
                            </>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )) : (
                <p className="text-sm text-slate-500 italic">No engineering signals found.</p>
              )}
            </div>
          </div>

          {/* Ownership Signals Section */}
          <div className="space-y-6">
            <h4 className="font-semibold text-slate-800 border-b border-slate-200 pb-2">
              Ownership & Leadership
            </h4>
            
            <div className="space-y-3">
              {ownershipSignals && ownershipSignals.length > 0 ? ownershipSignals.map((own, idx) => (
                <div key={idx} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                  <div className="flex flex-col gap-2">
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-sm font-bold text-slate-900">{own.signal}</span>
                    </div>
                    <div>
                      <OwnershipLevelBadge level={own.ownership_level} />
                    </div>
                    {own.evidence && own.evidence.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-100">
                        <span className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                          Sources
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {Array.from(new Set(own.evidence.map(e => e.source))).map(src => (
                            <EvidenceSourceBadge key={src} source={src} />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )) : (
                <p className="text-sm text-slate-500 italic">No ownership signals found.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </StateWrapper>
  );
}
