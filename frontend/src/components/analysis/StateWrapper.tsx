import React from 'react';
import { Loader2, AlertCircle, FileX } from 'lucide-react';

interface StateWrapperProps {
  isLoading: boolean;
  error?: Error | string | null;
  isEmpty: boolean;
  emptyTitle?: string;
  emptyMessage?: string;
  loadingMessage?: string;
  children: React.ReactNode;
}

export default function StateWrapper({
  isLoading,
  error,
  isEmpty,
  emptyTitle = "No Data Available",
  emptyMessage = "There is no data to display for this section.",
  loadingMessage = "Loading...",
  children,
}: StateWrapperProps) {
  if (isLoading) {
    return (
      <div className="flex min-h-[200px] w-full flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-slate-500">
        <Loader2 className="mb-4 h-8 w-8 animate-spin text-indigo-500" />
        <p className="text-sm font-medium">{loadingMessage}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[200px] w-full flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50 p-6 text-red-600">
        <AlertCircle className="mb-4 h-8 w-8" />
        <h3 className="mb-1 font-semibold">Failed to load data</h3>
        <p className="text-sm text-red-500 text-center">
          {error instanceof Error ? error.message : String(error)}
        </p>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="flex min-h-[200px] w-full flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-slate-500">
        <FileX className="mb-4 h-8 w-8 text-slate-400" />
        <h3 className="mb-1 font-semibold text-slate-900">{emptyTitle}</h3>
        <p className="text-sm text-center max-w-sm">{emptyMessage}</p>
      </div>
    );
  }

  return <>{children}</>;
}
