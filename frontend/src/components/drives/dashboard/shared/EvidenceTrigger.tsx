import React, { memo } from "react";
import { Evidence } from "@/types/drives";
import EvidenceBadge from "./EvidenceBadge";
import { useEvidence } from "./evidence/EvidenceContext";

interface EvidenceTriggerProps {
  evidence: Evidence[];
  title?: string;
  className?: string;
}

const EvidenceTrigger = memo(function EvidenceTrigger({ evidence, title, className = "" }: EvidenceTriggerProps) {
  const { openEvidence } = useEvidence();

  if (!evidence || evidence.length === 0) return null;

  const primaryEvidenceType = evidence[0].evidence_type;

  return (
    <div className={`relative inline-flex items-center ${className}`}>
      <EvidenceBadge 
        evidenceType={primaryEvidenceType}
        count={evidence.length}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          openEvidence(evidence, title);
        }}
        ariaExpanded={false}
      />
    </div>
  );
});

export default EvidenceTrigger;
