import React from "react";
import { useDriveSnapshot } from "../../context/SnapshotProvider";
import { Banknote, TrendingUp } from "lucide-react";

export default function CompensationSummaryCard() {
  const { snapshot } = useDriveSnapshot();
  // Assume first compensation object if array, or if it's a single object (depends on schema version, in v1.3 it's an array)
  const compensationList = snapshot?.intelligence_payload?.compensation || [];
  const comp = compensationList.length > 0 ? compensationList[0] : null;

  const formatLPA = (amount: number | null) => {
    if (amount === null) return "--";
    // Assuming amount is in absolute INR (e.g. 1300000) or already LPA. Let's assume absolute INR
    // If the system stores absolute numbers:
    if (amount > 1000) {
      return (amount / 100000).toFixed(1) + " LPA";
    }
    // If the system stores it as LPA already (e.g. 13.5):
    return amount.toFixed(1) + " LPA";
  };

  const formatCurrency = (amount: number | null, currency: string = "INR") => {
    if (amount === null) return "--";
    // Same heuristic: if it's large, format nicely, else just return
    if (amount > 1000) {
      return new Intl.NumberFormat('en-IN', { style: 'currency', currency, maximumFractionDigits: 0 }).format(amount);
    }
    return amount.toString();
  };

  return (
    <div className="flex flex-col h-full bg-indigo-600 border border-indigo-700 rounded-xl overflow-hidden shadow-sm hover:shadow transition-shadow">
      <div className="px-5 py-4 border-b border-indigo-500/50 flex items-center gap-2 bg-indigo-700/30">
        <Banknote className="h-4 w-4 text-indigo-200" />
        <h3 className="font-semibold text-indigo-50">Compensation</h3>
      </div>
      
      <div className="p-5 flex-1 flex flex-col justify-center">
        {!comp ? (
          <div className="text-center text-indigo-200">
            <p className="text-sm font-medium">Compensation Not Disclosed</p>
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            
            {/* CTC dominates hierarchy */}
            <div className="flex flex-col">
              <span className="text-indigo-200 text-xs font-bold uppercase tracking-wider mb-1">Total CTC</span>
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-extrabold text-white tracking-tight">
                  {formatLPA(comp.total_ctc)}
                </span>
              </div>
            </div>

            {/* Breakdown */}
            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-indigo-500/50">
              <div className="flex flex-col gap-1">
                <span className="text-indigo-200 text-xs font-bold uppercase tracking-wider">Fixed</span>
                <span className="text-indigo-50 font-semibold text-sm">
                  {comp.fixed_compensation ? formatLPA(comp.fixed_compensation) : "--"}
                </span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-indigo-200 text-xs font-bold uppercase tracking-wider">Variable</span>
                <span className="text-indigo-50 font-semibold text-sm">
                  {comp.variable_compensation ? formatLPA(comp.variable_compensation) : "--"}
                </span>
              </div>
              <div className="flex flex-col gap-1 col-span-2">
                <span className="text-indigo-200 text-xs font-bold uppercase tracking-wider">Joining Bonus</span>
                <span className="text-indigo-50 font-semibold text-sm">
                  {comp.joining_bonus ? formatCurrency(comp.joining_bonus, comp.currency) : "--"}
                </span>
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}
