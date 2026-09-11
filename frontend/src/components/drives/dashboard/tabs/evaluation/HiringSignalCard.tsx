import React from "react";
import { HiringSignal } from "@/types/drives";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { Radio } from "lucide-react";

interface HiringSignalCardProps {
  signal: HiringSignal;
}

export default function HiringSignalCard({ signal }: HiringSignalCardProps) {
  const isHighConfidence = signal.confidence === "HIGH";
  
  return (
    <div className={`flex flex-col p-4 border rounded-xl shadow-sm transition-shadow hover:shadow-md ${
      isHighConfidence ? "border-indigo-200 bg-white" : "border-slate-200 bg-slate-50/50"
    }`}>
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2.5">
          <div className={`p-1.5 rounded-lg ${
            isHighConfidence ? "bg-indigo-100 text-indigo-600" : "bg-slate-200 text-slate-600"
          }`}>
            <Radio className="h-4 w-4" />
          </div>
          <h4 className="font-semibold text-slate-800 text-sm leading-tight">
            {signal.signal.replace(/_/g, " ").replace(/\w\S*/g, w => w.charAt(0).toUpperCase() + w.substring(1).toLowerCase())}
          </h4>
        </div>
        <EvidenceTrigger evidence={signal.evidence} title={`Evidence for ${signal.signal}`} />
      </div>

      <div className="flex items-center gap-2 mt-auto pt-2">
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md ${
          isHighConfidence ? 'bg-indigo-100 text-indigo-700' : 'bg-slate-200 text-slate-600'
        }`}>
          {signal.confidence} Confidence
        </span>
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md ${
          signal.importance === "CRITICAL" ? 'text-rose-600 bg-rose-100' : 'text-slate-500 bg-slate-100'
        }`}>
          {signal.importance} Priority
        </span>
      </div>
    </div>
  );
}
