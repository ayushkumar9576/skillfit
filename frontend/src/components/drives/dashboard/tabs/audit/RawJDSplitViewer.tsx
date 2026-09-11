import React from "react";
import { useDrive } from "@/hooks/drives/useDrives";

interface RawJDSplitViewerProps {
  driveId: string;
}

export default function RawJDSplitViewer({ driveId }: RawJDSplitViewerProps) {
  const { data: drive } = useDrive(driveId);

  return (
    <div className="flex flex-col h-full bg-slate-900 rounded-xl overflow-hidden shadow-sm border border-slate-800">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-950">
        <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          Raw Job Description
        </h3>
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider bg-slate-800 px-2 py-0.5 rounded">Source Data</span>
      </div>
      <div className="p-4 overflow-y-auto max-h-[600px] font-mono text-sm leading-relaxed text-slate-300">
        {drive?.raw_job_description ? (
          <pre className="whitespace-pre-wrap font-mono text-xs">{drive.raw_job_description}</pre>
        ) : (
          <div className="text-center text-slate-600 mt-20 italic">No raw description available.</div>
        )}
      </div>
    </div>
  );
}
