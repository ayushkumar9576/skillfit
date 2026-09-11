import React from "react";
import { useDriveSnapshot } from "../../context/SnapshotProvider";
import { AlertTriangle, ShieldAlert, ShieldCheck } from "lucide-react";
import { ImportanceLevel, RiskIntelligence } from "@/types/drives";

export default function RiskAlertsCard() {
  const { snapshot } = useDriveSnapshot();
  const risks = snapshot?.intelligence_payload?.risks || [];
  const agreements = snapshot?.intelligence_payload?.service_agreements || [];

  // Determine highest severity risk
  const getSeverityWeight = (severity: ImportanceLevel) => {
    switch (severity) {
      case ImportanceLevel.critical: return 4;
      case ImportanceLevel.high: return 3;
      case ImportanceLevel.medium: return 2;
      case ImportanceLevel.low: return 1;
      default: return 0;
    }
  };

  const sortedRisks = [...risks].sort(
    (a, b) => getSeverityWeight(b.severity) - getSeverityWeight(a.severity)
  );
  
  const topRisk: RiskIntelligence | undefined = sortedRisks[0];
  const bond = agreements.find(a => a.has_bond);

  // Format currency roughly (Indian Rupees usually implied, but we can just use the raw number if currency isn't strictly defined in this struct, wait - let's assume raw numbers for now)
  const formatCurrency = (amount: number | null) => {
    if (amount === null) return "Unknown Penalty";
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
  };

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm hover:shadow transition-shadow">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50/50">
        <AlertTriangle className="h-4 w-4 text-rose-500" />
        <h3 className="font-semibold text-slate-800">Risks & Bonds</h3>
      </div>
      
      <div className="p-5 flex-1 flex flex-col gap-6">
        
        {/* Bond Information */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Service Agreement</h4>
          {bond ? (
            <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
              <ShieldAlert className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="flex flex-col">
                <span className="font-semibold text-amber-900 text-sm">
                  {bond.duration_months ? `${bond.duration_months} Month Bond` : 'Bond Required'}
                </span>
                <span className="text-xs text-amber-700 mt-0.5">
                  {bond.penalty_amount ? formatCurrency(bond.penalty_amount) + ' Penalty' : 'Penalty details unspecified'}
                </span>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-slate-600 p-2">
              <ShieldCheck className="h-4 w-4 text-emerald-500" />
              <span>No Service Bond</span>
            </div>
          )}
        </div>

        {/* Top Risk */}
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Primary Risk</h4>
          {topRisk ? (
            <div className="flex flex-col gap-1.5">
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold self-start ${
                topRisk.severity === ImportanceLevel.critical ? "bg-rose-100 text-rose-700" :
                topRisk.severity === ImportanceLevel.high ? "bg-orange-100 text-orange-700" :
                topRisk.severity === ImportanceLevel.medium ? "bg-amber-100 text-amber-700" :
                "bg-slate-100 text-slate-700"
              }`}>
                {topRisk.severity} SEVERITY
              </span>
              <span className="text-sm font-medium text-slate-800 capitalize leading-tight mt-1">
                {topRisk.risk.replace(/_/g, " ").toLowerCase()}
              </span>
              {sortedRisks.length > 1 && (
                <span className="text-xs text-slate-400 mt-1">
                  + {sortedRisks.length - 1} other risks identified
                </span>
              )}
            </div>
          ) : (
            <div className="text-sm text-slate-500 italic">
              No significant risks identified.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
