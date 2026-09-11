import React from "react";
import { useSnapshotHistory } from "@/hooks/drives/useSnapshots";
import { useDriveSnapshot } from "../context/SnapshotProvider";
import { Clock, ChevronDown } from "lucide-react";

interface SnapshotSelectorProps {
  driveId: string;
}

export default function SnapshotSelector({ driveId }: SnapshotSelectorProps) {
  const { data: historyData, isLoading } = useSnapshotHistory(driveId);
  const { selectedSnapshotId, setSelectedSnapshotId } = useDriveSnapshot();

  if (isLoading || !historyData || historyData.snapshots.length === 0) {
    return (
      <div className="h-14 w-64 bg-slate-100 rounded-lg animate-pulse" aria-hidden="true" />
    );
  }

  const snapshots = historyData.snapshots;
  // Sort descending by created_at assuming the backend doesn't already
  const sortedSnapshots = [...snapshots].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  
  const latestSnapshot = sortedSnapshots[0];
  
  // If selectedSnapshotId is null or "latest", use the latest snapshot's info for display
  const isLatestSelected = !selectedSnapshotId || selectedSnapshotId === "latest" || selectedSnapshotId === latestSnapshot.id;
  const currentDisplaySnapshot = isLatestSelected 
    ? latestSnapshot 
    : sortedSnapshots.find(s => s.id === selectedSnapshotId) || latestSnapshot;

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === latestSnapshot.id || val === "latest") {
      setSelectedSnapshotId("latest");
    } else {
      setSelectedSnapshotId(val);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="relative group">
      {/* 
        Native select overlaid on top of custom UI for fully accessible dropdown
        while maintaining the complex visual design requested.
      */}
      <select
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        value={isLatestSelected ? "latest" : selectedSnapshotId}
        onChange={handleChange}
        aria-label="Select Intelligence Snapshot"
      >
        <option value="latest">
          {latestSnapshot.analysis_version} (Latest)
        </option>
        {sortedSnapshots.map((snap) => {
          if (snap.id === latestSnapshot.id) return null; // Already handled by 'latest'
          return (
            <option key={snap.id} value={snap.id}>
              {snap.analysis_version} Historical
            </option>
          );
        })}
      </select>

      {/* Visual UI */}
      <div 
        className="flex items-center justify-between gap-4 p-3 bg-white border border-slate-200 rounded-lg shadow-sm group-hover:border-indigo-300 transition-colors"
        aria-hidden="true"
      >
        <div className="flex items-start gap-3">
          <div className={`mt-0.5 p-1.5 rounded-md ${isLatestSelected ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>
            <Clock className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold text-slate-900 flex items-center gap-2">
              Snapshot {currentDisplaySnapshot.analysis_version}
              {isLatestSelected && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                  Latest
                </span>
              )}
            </span>
            <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
              <span>Created {formatDate(currentDisplaySnapshot.created_at)}</span>
              <span className="w-1 h-1 bg-slate-300 rounded-full" />
              <span>Schema v{currentDisplaySnapshot.intelligence_schema_version || '1.0'}</span>
            </div>
          </div>
        </div>
        <ChevronDown className="h-4 w-4 text-slate-400 group-hover:text-indigo-500 transition-colors" />
      </div>
    </div>
  );
}
