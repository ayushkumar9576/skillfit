import React from "react";
import RawJDSplitViewer from "./RawJDSplitViewer";
import EvidenceExplorer from "./EvidenceExplorer";
import AnalysisMetadataPanel from "./AnalysisMetadataPanel";

interface AuditTabProps {
  driveId: string;
}

export default function AuditTab({ driveId }: AuditTabProps) {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <RawJDSplitViewer driveId={driveId} />
        <EvidenceExplorer />
      </div>
      <AnalysisMetadataPanel />
    </div>
  );
}
