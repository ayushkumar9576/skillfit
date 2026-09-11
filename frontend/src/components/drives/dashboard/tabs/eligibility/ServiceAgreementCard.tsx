import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { ShieldAlert, ShieldCheck } from "lucide-react";

export default function ServiceAgreementCard() {
  const { snapshot } = useDriveSnapshot();
  const agreements = snapshot?.intelligence_payload?.service_agreements;

  if (!agreements || agreements.length === 0) {
    return (
      <EmptyIntelligenceCard
        title="No Service Agreement Info"
        description="Bond or agreement criteria was not identified in this snapshot."
        icon={ShieldCheck}
      />
    );
  }

  // Assuming we care about the first one if multiple exist, or checking if any has a bond.
  const bond = agreements.find(a => a.has_bond) || agreements[0];

  const formatCurrency = (amount: number | null) => {
    if (amount === null) return "Unknown Penalty";
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
  };

  return (
    <div className={`flex flex-col h-full bg-white border rounded-xl overflow-hidden shadow-sm ${
      bond.has_bond ? 'border-amber-200' : 'border-slate-200'
    }`}>
      <div className={`px-5 py-4 border-b flex items-center justify-between ${
        bond.has_bond ? 'bg-amber-50 border-amber-100' : 'bg-slate-50 border-slate-100'
      }`}>
        <div className="flex items-center gap-2">
          {bond.has_bond ? (
            <ShieldAlert className="h-4 w-4 text-amber-600" />
          ) : (
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
          )}
          <h3 className={`font-semibold ${bond.has_bond ? 'text-amber-900' : 'text-slate-800'}`}>
            Service Agreement / Bond
          </h3>
        </div>
        <EvidenceTrigger evidence={bond.evidence} title="Agreement Evidence" />
      </div>
      
      <div className="p-5 flex flex-col gap-4">
        {bond.has_bond ? (
          <>
            <div className="flex flex-col gap-1">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-600">Bond Duration</span>
              <span className="text-2xl font-bold text-slate-800">
                {bond.duration_months ? `${bond.duration_months} Months` : 'Duration Unspecified'}
              </span>
            </div>
            
            <div className="flex flex-col gap-1 pt-4 border-t border-slate-100">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-600">Penalty Amount</span>
              <span className="text-xl font-bold text-slate-800">
                {bond.penalty_amount ? formatCurrency(bond.penalty_amount) : 'Amount Unspecified'}
              </span>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <ShieldCheck className="h-10 w-10 text-emerald-400 mb-3" />
            <h4 className="text-lg font-bold text-slate-800">No Bond Required</h4>
            <p className="text-sm text-slate-500 mt-1">There is no explicit service agreement identified.</p>
          </div>
        )}
      </div>
    </div>
  );
}
