import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { Clock, Moon, Sun, RotateCcw } from "lucide-react";

export default function ShiftIntelligenceCard() {
  const { snapshot } = useDriveSnapshot();
  const shift = snapshot?.intelligence_payload?.shift_intelligence;

  if (!shift) {
    return (
      <EmptyIntelligenceCard
        title="No Shift Info"
        description="Shift details were not identified."
        icon={Clock}
      />
    );
  }

  const formatShiftType = (type: string) => {
    switch(type) {
      case "NIGHT_SHIFT": return { label: "Night Shift", icon: Moon, color: "text-indigo-500", bg: "bg-indigo-50" };
      case "ROTATIONAL_SHIFT": return { label: "Rotational Shift", icon: RotateCcw, color: "text-orange-500", bg: "bg-orange-50" };
      case "GENERAL_SHIFT": return { label: "General Shift", icon: Sun, color: "text-emerald-500", bg: "bg-emerald-50" };
      default: return { label: type.replace(/_/g, " "), icon: Clock, color: "text-slate-500", bg: "bg-slate-50" };
    }
  };

  const style = formatShiftType(shift.shift_type);
  const Icon = style.icon;

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-blue-500" />
          <h3 className="font-semibold text-slate-800">Shift Intelligence</h3>
        </div>
        <EvidenceTrigger evidence={shift.evidence} title="Shift Evidence" />
      </div>
      
      <div className="p-5 flex flex-col gap-6">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-xl ${style.bg} ${style.color}`}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-0.5">Shift Expected</span>
            <span className="text-xl font-bold text-slate-800">{style.label}</span>
          </div>
        </div>

        {shift.details && (
          <div className="flex flex-col gap-2 pt-4 border-t border-slate-100">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Details</span>
            <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
              {shift.details}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
