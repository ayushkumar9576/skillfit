import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import EmptyIntelligenceCard from "../../../shared/EmptyIntelligenceCard";
import EvidenceTrigger from "../../../shared/EvidenceTrigger";
import { MapPin, Globe, Building2, Home } from "lucide-react";

export default function WorkArrangementCard() {
  const { snapshot } = useDriveSnapshot();
  const arrangement = snapshot?.intelligence_payload?.work_arrangement;

  if (!arrangement) {
    return (
      <EmptyIntelligenceCard
        title="No Work Arrangement Info"
        description="Location and work arrangement details were not identified."
        icon={MapPin}
      />
    );
  }

  const formatArrangementType = (type: string) => {
    switch(type) {
      case "REMOTE": return { label: "Remote", icon: Globe, color: "text-blue-500", bg: "bg-blue-50" };
      case "HYBRID": return { label: "Hybrid", icon: Home, color: "text-purple-500", bg: "bg-purple-50" };
      case "ON_SITE": return { label: "Onsite", icon: Building2, color: "text-indigo-500", bg: "bg-indigo-50" };
      default: return { label: type.replace(/_/g, " "), icon: MapPin, color: "text-slate-500", bg: "bg-slate-50" };
    }
  };

  const style = formatArrangementType(arrangement.arrangement_type);
  const Icon = style.icon;

  return (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-rose-500" />
          <h3 className="font-semibold text-slate-800">Work Arrangement</h3>
        </div>
        <EvidenceTrigger evidence={arrangement.evidence} title="Arrangement Evidence" />
      </div>
      
      <div className="p-5 flex flex-col gap-6">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-xl ${style.bg} ${style.color}`}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-0.5">Arrangement Type</span>
            <span className="text-xl font-bold text-slate-800">{style.label}</span>
          </div>
        </div>

        {arrangement.locations && arrangement.locations.length > 0 && (
          <div className="flex flex-col gap-2 pt-4 border-t border-slate-100">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Locations</span>
            <div className="flex flex-wrap gap-2">
              {arrangement.locations.map((loc, idx) => (
                <span key={idx} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-slate-50 text-slate-700 border border-slate-200">
                  <MapPin className="h-3.5 w-3.5 text-slate-400" />
                  {loc}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
