import React from "react";
import { useDriveSnapshot } from "../../../context/SnapshotProvider";
import { Info, Clock, Code, FileJson } from "lucide-react";

export default function AnalysisMetadataPanel() {
  const { snapshot } = useDriveSnapshot();

  if (!snapshot) return null;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4 pb-4 border-b border-slate-200">
        <Info className="h-5 w-5 text-indigo-500" />
        <h3 className="font-semibold text-slate-800">Snapshot Metadata</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <Clock className="h-3 w-3" /> Created At
          </span>
          <span className="text-sm font-mono text-slate-700">{formatDate(snapshot.created_at)}</span>
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <Code className="h-3 w-3" /> Analysis Version
          </span>
          <span className="text-sm font-mono text-slate-700 bg-white px-2 py-0.5 rounded border inline-flex self-start">
            v{snapshot.analysis_version}
          </span>
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <FileJson className="h-3 w-3" /> Schema Version
          </span>
          <span className="text-sm font-mono text-slate-700">
            {snapshot.intelligence_payload?.intelligence_schema_version || "Unknown"}
          </span>
        </div>

        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <FileJson className="h-3 w-3" /> Prompt Version
          </span>
          <span className="text-sm font-mono text-slate-700">
            {snapshot.prompt_version}
          </span>
        </div>
      </div>
    </div>
  );
}
