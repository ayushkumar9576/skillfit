import React from "react";
import LoadingState from "@/components/shared/LoadingState";

export default function DashboardLoadingState() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center p-8 bg-slate-50/50 rounded-xl border border-slate-100">
      <LoadingState message="Loading Drive Intelligence..." />
    </div>
  );
}
