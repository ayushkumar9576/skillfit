import React from "react";
import ErrorState from "@/components/shared/ErrorState";

interface DashboardErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function DashboardErrorState({ message = "Failed to load dashboard data.", onRetry }: DashboardErrorStateProps) {
  return (
    <div className="p-8 max-w-2xl mx-auto mt-12">
      <ErrorState message={message} retryAction={onRetry} />
    </div>
  );
}
