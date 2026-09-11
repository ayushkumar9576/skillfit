import React from "react";
import { SuccessIndicator } from "@/types/drives";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { Trophy } from "lucide-react";

interface SuccessIndicatorCardProps {
  indicator: SuccessIndicator;
}

export default function SuccessIndicatorCard({ indicator }: SuccessIndicatorCardProps) {
  const isRequired = indicator.strength === "REQUIRED";
  const isBonus = indicator.strength === "BONUS";

  return (
    <div className={`flex flex-col p-4 border rounded-xl shadow-sm transition-shadow hover:shadow-md ${
      isRequired ? "border-amber-200 bg-amber-50/30" : 
      isBonus ? "border-emerald-200 bg-emerald-50/30" :
      "border-slate-200 bg-white"
    }`}>
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2.5">
          <div className={`p-1.5 rounded-lg ${
            isRequired ? "bg-amber-100 text-amber-600" : 
            isBonus ? "bg-emerald-100 text-emerald-600" :
            "bg-slate-100 text-slate-600"
          }`}>
            <Trophy className="h-4 w-4" />
          </div>
          <h4 className="font-semibold text-slate-800 text-sm leading-tight">
            {indicator.indicator.replace(/_/g, " ").replace(/\w\S*/g, w => w.charAt(0).toUpperCase() + w.substring(1).toLowerCase())}
          </h4>
        </div>
        <EvidenceTrigger evidence={indicator.evidence} title={`Evidence for ${indicator.indicator}`} />
      </div>

      <div className="mt-auto pt-2">
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md ${
          isRequired ? 'bg-amber-100 text-amber-700' : 
          isBonus ? 'bg-emerald-100 text-emerald-700' :
          'bg-slate-200 text-slate-700'
        }`}>
          {indicator.strength} Expectation
        </span>
      </div>
    </div>
  );
}
