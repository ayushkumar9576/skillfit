import React, { useMemo } from "react";
import { DriveResponse } from "@/types/drives";
import { History, X } from "lucide-react";
import { useAnalysisHistory } from "@/hooks/drives/useAnalysis";
import SnapshotVersionCard from "./SnapshotVersionCard";

interface SnapshotHistoryDrawerProps {
  driveId: string;
  drive: DriveResponse | undefined;
  isOpen: boolean;
  onClose: () => void;
}

export default function SnapshotHistoryDrawer({ driveId, drive, isOpen, onClose }: SnapshotHistoryDrawerProps) {
  const { data: history, isLoading } = useAnalysisHistory(driveId, drive);

  // Focus trap logic can be added here similar to EvidenceModal
  // For brevity, skipping full trap, focusing on UI structure.

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex justify-end">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200" 
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="relative w-full max-w-md bg-slate-50 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-300">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-white z-10">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-indigo-500" />
            <h2 className="text-lg font-semibold text-slate-800">Snapshot History</h2>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-100 p-1.5 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex justify-center py-10">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            </div>
          ) : history?.analyses && history.analyses.length > 0 ? (
            <div className="relative border-l-2 border-slate-200 ml-4 space-y-8 pb-8">
              {history.analyses.map((snapshot, idx) => {
                const previousSnapshot = idx < history.analyses.length - 1 ? history.analyses[idx + 1] : undefined;
                return (
                  <SnapshotVersionCard 
                    key={snapshot.id} 
                    snapshot={snapshot} 
                    previousSnapshot={previousSnapshot}
                    isLatest={idx === 0} 
                  />
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <History className="h-10 w-10 mx-auto text-slate-300 mb-2" />
              <p>No historical snapshots available.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
