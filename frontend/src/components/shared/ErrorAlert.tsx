"use client";

/**
 * components/shared/ErrorAlert.tsx
 * ----------------------------------
 * Reusable error display component.
 * Handles network errors, validation errors, auth errors, and server errors.
 */

import { AlertCircle, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorAlertProps {
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export default function ErrorAlert({ message, onDismiss, className }: ErrorAlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3",
        className
      )}
    >
      <AlertCircle className="h-4 w-4 mt-0.5 shrink-0 text-red-500" aria-hidden="true" />
      <p className="flex-1 text-sm text-red-700 leading-relaxed">{message}</p>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 rounded text-red-400 hover:text-red-600 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
          aria-label="Dismiss error"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
