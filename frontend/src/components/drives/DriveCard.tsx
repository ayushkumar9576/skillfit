import React from "react";
import Link from "next/link";
import { format } from "date-fns";
import { Briefcase, Building2, Calendar, IndianRupee } from "lucide-react";

export type DriveStatusType = "draft" | "analyzing" | "analysis_failed" | "ready" | "published" | "archived";

export interface DriveCardProps {
  drive: {
    id: string;
    company_name: string;
    role: string;
    package?: string | null;
    status: DriveStatusType;
    created_at: string | Date;
  };
}

const statusConfig: Record<DriveStatusType, { label: string; colors: string }> = {
  draft: { label: "Draft", colors: "bg-slate-100 text-slate-700 border-slate-200" },
  analyzing: { label: "Analyzing", colors: "bg-blue-50 text-blue-700 border-blue-200" },
  analysis_failed: { label: "Failed", colors: "bg-red-50 text-red-700 border-red-200" },
  ready: { label: "Ready", colors: "bg-purple-50 text-purple-700 border-purple-200" },
  published: { label: "Published", colors: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  archived: { label: "Archived", colors: "bg-slate-100 text-slate-500 border-slate-200" },
};

export default function DriveCard({ drive }: DriveCardProps) {
  const config = statusConfig[drive.status] || statusConfig.draft;

  return (
    <Link
      href={`/admin/drives/${drive.id}`}
      className="block bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md hover:border-indigo-300 transition-all duration-200 group"
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0 group-hover:bg-indigo-100 transition-colors">
            <Building2 className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">
              {drive.company_name}
            </h3>
            <div className="flex items-center gap-1.5 text-sm text-slate-500 mt-0.5">
              <Briefcase className="w-3.5 h-3.5" />
              <span>{drive.role}</span>
            </div>
          </div>
        </div>
        <span className={`px-2.5 py-1 text-xs font-medium rounded-full border ${config.colors}`}>
          {config.label}
        </span>
      </div>

      <div className="flex items-center gap-4 text-sm text-slate-500 pt-4 border-t border-slate-100">
        <div className="flex items-center gap-1.5">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span>Created {format(new Date(drive.created_at), "MMM d, yyyy")}</span>
        </div>
        {drive.package && (
          <div className="flex items-center gap-1.5">
            <IndianRupee className="w-4 h-4 text-slate-400" />
            <span>{drive.package}</span>
          </div>
        )}
      </div>
    </Link>
  );
}
