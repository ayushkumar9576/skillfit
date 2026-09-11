import React, { useState, useEffect } from "react";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { useDriveSnapshot } from "../context/SnapshotProvider";

export default function HistoricalSnapshotBanner() {
  const { isHistoricalView, snapshot, setSelectedSnapshotId } = useDriveSnapshot();
  const [isVisible, setIsVisible] = useState(isHistoricalView);

  // Sync visibility with context state
  useEffect(() => {
    setIsVisible(isHistoricalView);
  }, [isHistoricalView]);

  if (!isVisible || !isHistoricalView || !snapshot) return null;

  const handleSwitchToLatest = () => {
    setSelectedSnapshotId("latest");
  };

  const handleDismiss = () => {
    setIsVisible(false);
  };

  return (
    <div className="bg-amber-50 border-x border-b border-amber-200 rounded-b-xl shadow-sm px-4 py-3 flex items-center justify-between mb-6 mx-4 sm:mx-6 lg:mx-8">
      <div className="flex items-center gap-3">
        <div className="p-1.5 bg-amber-100 rounded text-amber-700">
          <AlertTriangle className="h-4 w-4" />
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 text-sm">
          <span className="font-semibold text-amber-900">Viewing Historical Snapshot</span>
          <span className="hidden sm:inline w-1 h-1 bg-amber-300 rounded-full" />
          <span className="text-amber-700">
            Version {snapshot.analysis_version} ({new Date(snapshot.created_at).toLocaleDateString()})
          </span>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <button 
          onClick={handleSwitchToLatest}
          className="text-sm font-bold text-amber-700 hover:text-amber-900 flex items-center gap-1 group"
        >
          Switch to Latest
          <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
        </button>
        <button 
          onClick={handleDismiss}
          className="text-amber-400 hover:text-amber-600 p-1"
          aria-label="Dismiss banner"
        >
          &times;
        </button>
      </div>
    </div>
  );
}
