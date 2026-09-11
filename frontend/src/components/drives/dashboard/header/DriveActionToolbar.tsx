import React from "react";
import { Sparkles, Send, Download } from "lucide-react";
import { useTriggerAnalysis } from "@/hooks/drives/useAnalysis";
import { DriveStatus } from "@/types/drives";

interface DriveActionToolbarProps {
  driveId: string;
  driveStatus: DriveStatus;
}

export default function DriveActionToolbar({ driveId, driveStatus }: DriveActionToolbarProps) {
  const { mutate: triggerAnalysis, isPending: isTriggering } = useTriggerAnalysis(driveId);

  const handleRerunAnalysis = () => {
    triggerAnalysis();
  };

  const handlePublishDrive = () => {
    // Placeholder for publish action
    console.log("Publish drive triggered for", driveId);
  };

  const handleExportIntelligence = () => {
    // Placeholder for export action
    console.log("Export intelligence triggered for", driveId);
  };

  const isAnalyzing = driveStatus === DriveStatus.analyzing;

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        onClick={handleRerunAnalysis}
        disabled={isAnalyzing || isTriggering}
        className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-sm font-medium transition-colors shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
      >
        <Sparkles className={`h-4 w-4 ${isTriggering ? 'animate-pulse text-indigo-500' : 'text-slate-500'}`} />
        {isTriggering ? 'Triggering...' : 'Re-run Analysis'}
      </button>
      
      <button
        onClick={handleExportIntelligence}
        className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded-lg text-sm font-medium transition-colors shadow-sm"
      >
        <Download className="h-4 w-4 text-slate-500" />
        Export
      </button>

      <button
        onClick={handlePublishDrive}
        disabled={driveStatus === DriveStatus.published || isAnalyzing}
        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white border border-transparent rounded-lg text-sm font-medium transition-colors shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
      >
        <Send className="h-4 w-4" />
        {driveStatus === DriveStatus.published ? 'Published' : 'Publish Drive'}
      </button>
    </div>
  );
}
