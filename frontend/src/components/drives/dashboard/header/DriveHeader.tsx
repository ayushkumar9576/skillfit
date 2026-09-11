import React from "react";
import { DriveResponse } from "@/types/drives";
import CompanyIdentityBlock from "./CompanyIdentityBlock";
import DriveStatusBadge from "./DriveStatusBadge";
import SnapshotSelector from "./SnapshotSelector";
import DriveActionToolbar from "./DriveActionToolbar";
import HistoricalSnapshotBanner from "./HistoricalSnapshotBanner";

interface DriveHeaderProps {
  drive: DriveResponse;
}

export default function DriveHeader({ drive }: DriveHeaderProps) {
  return (
    <div className="flex flex-col bg-white border-b border-slate-200">
      <div className="px-4 py-6 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
          
          {/* Left Column: Identity & Status */}
          <div className="flex flex-col gap-4">
            <div className="flex items-start gap-4">
              <CompanyIdentityBlock drive={drive} />
              <div className="mt-1">
                <DriveStatusBadge status={drive.status} />
              </div>
            </div>
          </div>

          {/* Right Column: Actions & Selectors */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 lg:shrink-0 mt-2 lg:mt-0">
            <SnapshotSelector driveId={drive.id} />
            <div className="hidden sm:block w-px h-10 bg-slate-200 mx-2" aria-hidden="true" />
            <DriveActionToolbar driveId={drive.id} driveStatus={drive.status} />
          </div>

        </div>
      </div>

      {/* Renders banner conditionally based on context */}
      <HistoricalSnapshotBanner />
    </div>
  );
}
