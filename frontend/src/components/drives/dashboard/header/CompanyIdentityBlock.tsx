import React from "react";
import { DriveResponse } from "@/types/drives";
import { useDriveSnapshot } from "../context/SnapshotProvider";

interface CompanyIdentityBlockProps {
  drive: DriveResponse;
}

export default function CompanyIdentityBlock({ drive }: CompanyIdentityBlockProps) {
  const { snapshot } = useDriveSnapshot();
  const domainIntelligence = snapshot?.intelligence_payload?.domain;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          {drive.company_name}
        </h1>
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
          {drive.placement_season}
        </span>
      </div>
      
      <div className="flex flex-wrap items-center gap-2 mt-1">
        <span className="text-lg font-medium text-slate-700">
          {drive.role}
        </span>
        
        {/* Domain Badges */}
        {domainIntelligence && (
          <>
            <span className="w-1.5 h-1.5 rounded-full bg-slate-300 mx-1"></span>
            
            {domainIntelligence.industry && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                {domainIntelligence.industry.replace(/_/g, " ")}
              </span>
            )}
            
            {domainIntelligence.role_family && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                {domainIntelligence.role_family}
              </span>
            )}

            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-700 border border-purple-100">
              {domainIntelligence.domain.replace(/_/g, " ")}
            </span>
          </>
        )}
      </div>
    </div>
  );
}
