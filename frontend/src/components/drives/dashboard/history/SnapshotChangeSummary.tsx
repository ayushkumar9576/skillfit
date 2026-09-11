import React, { useMemo } from "react";
import { SnapshotSummaryResponse } from "@/types/drives";
import { ArrowRight, Plus, Minus, GitCommit } from "lucide-react";

interface SnapshotChangeSummaryProps {
  current: SnapshotSummaryResponse;
  previous?: SnapshotSummaryResponse;
}

export default function SnapshotChangeSummary({ current, previous }: SnapshotChangeSummaryProps) {
  const diffs = useMemo(() => {
    if (!previous) return null; // Initial snapshot has no previous to diff against

    const changes: React.ReactNode[] = [];

    // 1. Difficulty Change
    const currDiff = (current as any).intelligence_payload?.difficulty?.level;
    const prevDiff = (previous as any).intelligence_payload?.difficulty?.level;
    if (currDiff && prevDiff && currDiff !== prevDiff) {
      changes.push(
        <div key="diff" className="flex items-center gap-2 text-sm">
          <span className="text-slate-500 font-medium w-24">Difficulty:</span>
          <span className="text-slate-400 line-through text-xs">{prevDiff.replace(/_/g, " ")}</span>
          <ArrowRight className="h-3 w-3 text-slate-400" />
          <span className="font-semibold text-slate-700 text-xs bg-slate-100 px-1.5 py-0.5 rounded">
            {currDiff.replace(/_/g, " ")}
          </span>
        </div>
      );
    }

    // 2. Technology Counts
    const currTechs = (current as any).intelligence_payload?.technologies?.map((t: any) => t.name) || [];
    const prevTechs = (previous as any).intelligence_payload?.technologies?.map((t: any) => t.name) || [];
    
    const addedTechs = currTechs.filter(t => !prevTechs.includes(t));
    const removedTechs = prevTechs.filter(t => !currTechs.includes(t));

    if (addedTechs.length > 0) {
      changes.push(
        <div key="added-tech" className="flex items-start gap-2 text-sm mt-1">
          <span className="text-slate-500 font-medium w-24 flex items-center gap-1 mt-0.5">
            <Plus className="h-3 w-3 text-emerald-500" /> Tech Added:
          </span>
          <div className="flex flex-wrap gap-1 flex-1">
            {addedTechs.slice(0, 3).map(t => (
              <span key={t} className="text-xs bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded border border-emerald-100">{t}</span>
            ))}
            {addedTechs.length > 3 && <span className="text-xs text-slate-400">+{addedTechs.length - 3} more</span>}
          </div>
        </div>
      );
    }

    if (removedTechs.length > 0) {
      changes.push(
        <div key="removed-tech" className="flex items-start gap-2 text-sm mt-1">
          <span className="text-slate-500 font-medium w-24 flex items-center gap-1 mt-0.5">
            <Minus className="h-3 w-3 text-rose-500" /> Tech Removed:
          </span>
          <div className="flex flex-wrap gap-1 flex-1">
            {removedTechs.slice(0, 3).map(t => (
              <span key={t} className="text-xs bg-rose-50 text-rose-700 px-1.5 py-0.5 rounded border border-rose-100 line-through opacity-70">{t}</span>
            ))}
            {removedTechs.length > 3 && <span className="text-xs text-slate-400">+{removedTechs.length - 3} more</span>}
          </div>
        </div>
      );
    }

    // 3. Qualifications Count Change (Simple heuristic)
    const currQuals = (current as any).intelligence_payload?.qualifications?.length || 0;
    const prevQuals = (previous as any).intelligence_payload?.qualifications?.length || 0;
    if (currQuals !== prevQuals) {
      changes.push(
        <div key="quals" className="flex items-center gap-2 text-sm mt-1">
          <span className="text-slate-500 font-medium w-24">Qualifications:</span>
          <span className="text-slate-600 text-xs">Changed from {prevQuals} to {currQuals} rules</span>
        </div>
      );
    }

    return changes;
  }, [current, previous]);

  if (!previous) {
    return (
      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-500">
        <GitCommit className="h-3 w-3" /> Initial Baseline Snapshot
      </div>
    );
  }

  if (diffs && diffs.length > 0) {
    return (
      <div className="mt-3 pt-3 border-t border-slate-100 flex flex-col gap-1">
        {diffs}
      </div>
    );
  }

  return (
    <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-400 italic">
      No significant business intelligence changes detected from previous version.
    </div>
  );
}
