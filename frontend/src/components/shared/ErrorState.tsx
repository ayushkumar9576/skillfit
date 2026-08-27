import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message: string;
  retryAction?: () => void;
  className?: string;
}

export default function ErrorState({ title = "Something went wrong", message, retryAction, className }: ErrorStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center rounded-2xl border border-red-200 bg-red-50 p-8 text-center", className)}>
      <AlertCircle className="h-10 w-10 text-red-500 mb-4" />
      <h3 className="text-lg font-semibold text-red-900">{title}</h3>
      <p className="mt-2 text-sm text-red-700 max-w-sm">{message}</p>
      {retryAction && (
        <button
          onClick={retryAction}
          className="mt-6 rounded-md bg-red-100 px-4 py-2 text-sm font-semibold text-red-800 hover:bg-red-200 transition-colors"
        >
          Try Again
        </button>
      )}
    </div>
  );
}
