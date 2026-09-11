import React, { memo } from "react";
import { QualificationIntelligence } from "@/types/drives";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { ShieldAlert, Shield } from "lucide-react";

interface QualificationRowProps {
  qualification: QualificationIntelligence;
  isHardGate: boolean;
}

const QualificationRow = memo(function QualificationRow({ qualification, isHardGate }: QualificationRowProps) {
  const formatType = (type: string) => type.replace(/_/g, " ").replace(/\w\S*/g, w => w.charAt(0).toUpperCase() + w.substring(1).toLowerCase());
  
  const formatValue = () => {
    let result = "";
    if (qualification.operator !== "EQ") {
      result += qualification.operator + " ";
    }
    if (qualification.numeric_value !== null) {
      result += qualification.numeric_value;
    }
    if (qualification.allowed_values && qualification.allowed_values.length > 0) {
      result += qualification.allowed_values.join(", ");
    }
    return result;
  };

  return (
    <div className={`flex flex-col sm:flex-row sm:items-center justify-between p-4 border-l-4 rounded-r-xl transition-all gap-3 sm:gap-0 ${
      isHardGate 
        ? "bg-rose-50/50 border-rose-500 hover:bg-rose-50" 
        : "bg-blue-50/50 border-blue-400 hover:bg-blue-50"
    }`}>
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          {isHardGate ? (
            <ShieldAlert className="h-4 w-4 text-rose-500" />
          ) : (
            <Shield className="h-4 w-4 text-blue-500" />
          )}
          <span className="font-semibold text-slate-800">
            {formatType(qualification.qualification_type)}
          </span>
          <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ml-2 ${
            isHardGate ? "bg-rose-100 text-rose-700" : "bg-blue-100 text-blue-700"
          }`}>
            {isHardGate ? "Hard Gate" : "Preference"}
          </span>
        </div>
        <div className="text-sm font-medium text-slate-600 mt-1 pl-6">
          Requirement: <span className="text-slate-900">{formatValue()}</span>
        </div>
      </div>
      
      <div className="self-end sm:self-auto">
        <EvidenceTrigger evidence={qualification.evidence} title={`Evidence for ${formatType(qualification.qualification_type)}`} />
      </div>
    </div>
  );
});

export default QualificationRow;
