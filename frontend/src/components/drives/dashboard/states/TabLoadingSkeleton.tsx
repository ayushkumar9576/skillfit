import React from "react";
import { Loader2 } from "lucide-react";

export default function TabLoadingSkeleton() {
  return (
    <div className="w-full animate-pulse space-y-6">
      {/* Skeleton Top Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-100 h-64 rounded-xl border border-slate-200"></div>
        <div className="bg-slate-100 h-64 rounded-xl border border-slate-200"></div>
      </div>
      
      {/* Skeleton Middle Section */}
      <div className="bg-slate-100 h-40 rounded-xl border border-slate-200"></div>

      <div className="flex justify-center py-6 text-slate-400">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    </div>
  );
}
