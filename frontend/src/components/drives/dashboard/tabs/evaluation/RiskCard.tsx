import React, { memo } from "react";
import { RiskIntelligence } from "@/types/drives";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { AlertTriangle } from "lucide-react";

interface RiskCardProps {
  risk: RiskIntelligence;
}

const RiskCard = memo(function RiskCard({ risk }: RiskCardProps) {
  const getSeverityStyle = (sev: string) => {
    switch (sev) {
      case "CRITICAL": return "border-rose-300 bg-rose-50/50";
      case "HIGH": return "border-orange-300 bg-orange-50/50";
      case "MEDIUM": return "border-amber-300 bg-amber-50/50";
      case "LOW": return "border-slate-300 bg-slate-50/50";
      default: return "border-slate-200 bg-white";
    }
  };

  const getBadgeStyle = (sev: string) => {
    switch (sev) {
      case "CRITICAL": return "bg-rose-100 text-rose-700";
      case "HIGH": return "bg-orange-100 text-orange-700";
      case "MEDIUM": return "bg-amber-100 text-amber-700";
      case "LOW": return "bg-slate-100 text-slate-700";
      default: return "bg-slate-100 text-slate-700";
    }
  };

  return (
    <div className={`flex flex-col p-4 border rounded-xl shadow-sm transition-shadow hover:shadow-md ${getSeverityStyle(risk.severity)}`}>
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2.5">
          <AlertTriangle className={`h-5 w-5 ${risk.severity === 'CRITICAL' ? 'text-rose-500' : 'text-slate-500'}`} />
          <h4 className="font-semibold text-slate-800 text-base leading-tight">
            {risk.risk.replace(/_/g, " ").replace(/\w\S*/g, w => w.charAt(0).toUpperCase() + w.substring(1).toLowerCase())}
          </h4>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md ${getBadgeStyle(risk.severity)}`}>
            {risk.severity} Severity
          </span>
          <EvidenceTrigger evidence={risk.evidence} title={`Evidence for ${risk.risk}`} />
        </div>
      </div>
    </div>
  );
});

export default RiskCard;
