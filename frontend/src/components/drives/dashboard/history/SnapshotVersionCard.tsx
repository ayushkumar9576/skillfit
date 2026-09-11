import React from "react";
import { SnapshotSummaryResponse } from "@/types/drives";
import { CheckCircle2, Clock } from "lucide-react";
import SnapshotChangeSummary from "./SnapshotChangeSummary";
import { useDriveSnapshot } from "../context/SnapshotProvider";

interface SnapshotVersionCardProps {
  snapshot: SnapshotSummaryResponse;
  previousSnapshot?: SnapshotSummaryResponse;
  isLatest: boolean;
}

export default function SnapshotVersionCard({ snapshot, previousSnapshot, isLatest }: SnapshotVersionCardProps) {
  const { selectedSnapshotId, setSelectedSnapshotId } = useDriveSnapshot();
  
  const isSelected = selectedSnapshotId === snapshot.id || (selectedSnapshotId === 'latest' && isLatest);
  
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <div className="relative pl-6">
      {/* Timeline dot */}
      <div className={`absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 ${
        isLatest ? "bg-indigo-500 border-white ring-2 ring-indigo-200" : "bg-slate-300 border-white"
      }`} />
      
      <div className={`p-4 rounded-xl border transition-all ${
        isSelected ? "bg-white border-indigo-300 shadow-sm ring-1 ring-indigo-100" : "bg-white/60 border-slate-200 hover:bg-white hover:border-slate-300"
      }`}>
        <div className="flex items-start justify-between mb-2">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-800">Version {snapshot.analysis_version}</span>
              {isLatest && <span className="text-[10px] bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded font-bold uppercase">Latest</span>}
            </div>
            <span className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
              <Clock className="h-3 w-3" /> {formatDate(snapshot.created_at)}
            </span>
          </div>
          
          <button 
            onClick={() => setSelectedSnapshotId(isLatest ? 'latest' : snapshot.id)}
            disabled={isSelected}
            className={`text-xs font-semibold px-2.5 py-1 rounded-md transition-colors ${
              isSelected 
                ? "bg-emerald-50 text-emerald-700 cursor-default" 
                : "bg-slate-100 text-slate-600 hover:bg-indigo-50 hover:text-indigo-700"
            }`}
          >
            {isSelected ? (
              <span className="flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> Viewing</span>
            ) : "View Snapshot"}
          </button>
        </div>

        {/* Diff Summary */}
        <SnapshotChangeSummary current={snapshot} previous={previousSnapshot} />
        
      </div>
    </div>
  );
}
