import React from "react";
import { VerificationStatus } from "@/types/candidate-profile";

interface VerificationStatusBadgeProps {
  status: VerificationStatus | string;
  className?: string;
}

export default function VerificationStatusBadge({ status, className = "" }: VerificationStatusBadgeProps) {
  const getStyle = () => {
    switch (status) {
      case VerificationStatus.STRONGLY_VERIFIED:
        return "bg-emerald-100 text-emerald-800 ring-emerald-600/20";
      case VerificationStatus.VERIFIED:
        return "bg-blue-100 text-blue-800 ring-blue-600/20";
      case VerificationStatus.WEAKLY_VERIFIED:
        return "bg-amber-100 text-amber-800 ring-amber-600/20";
      case VerificationStatus.UNVERIFIED:
      default:
        return "bg-slate-100 text-slate-800 ring-slate-600/10";
    }
  };

  const label = typeof status === "string" ? status.replace(/_/g, " ") : "UNKNOWN";

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${getStyle()} ${className}`}>
      {label}
    </span>
  );
}
