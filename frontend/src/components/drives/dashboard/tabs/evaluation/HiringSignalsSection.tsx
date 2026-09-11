import React, { useMemo } from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import HiringSignalCard from "./HiringSignalCard";
import { Radio } from "lucide-react";

export default function HiringSignalsSection() {
  const { snapshot } = useDriveSnapshot();
  const signals = snapshot?.intelligence_payload?.hiring_signals;

  const sortedSignals = useMemo(() => {
    if (!signals) return [];
    
    const getWeight = (imp: string, conf: string) => {
      let weight = 0;
      if (imp === "CRITICAL") weight += 10;
      if (imp === "HIGH") weight += 5;
      if (conf === "HIGH") weight += 2;
      return weight;
    };

    return [...signals].sort((a, b) => getWeight(b.importance, b.confidence) - getWeight(a.importance, a.confidence));
  }, [signals]);

  if (!sortedSignals || sortedSignals.length === 0) {
    return (
      <EmptyIntelligenceCard
        title="No Hiring Signals"
        description="The intelligence engine did not identify implicit hiring signals from this drive description."
        icon={Radio}
      />
    );
  }

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden h-full">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2 bg-slate-50">
        <Radio className="h-4 w-4 text-indigo-500" />
        <h3 className="font-semibold text-slate-800">Implicit Hiring Signals</h3>
      </div>
      <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
        {sortedSignals.map((signal, idx) => (
          <HiringSignalCard key={`${signal.signal}-${idx}`} signal={signal} />
        ))}
      </div>
    </div>
  );
}
