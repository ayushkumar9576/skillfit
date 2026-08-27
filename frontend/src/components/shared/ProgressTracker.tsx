import { cn } from "@/lib/utils";
import { CheckCircle2, Circle, Clock } from "lucide-react";

type ProcessingStatus = "uploaded" | "processing" | "completed" | "failed";

interface ProgressTrackerProps {
  status: ProcessingStatus;
  className?: string;
}

export default function ProgressTracker({ status, className }: ProgressTrackerProps) {
  const steps = [
    { id: "uploaded", label: "Uploaded" },
    { id: "admin_approval", label: "Awaiting Admin Approval" },
    { id: "processing", label: "Processing" },
    { id: "completed", label: "Completed" },
  ];

  // Determine active step index
  let activeIndex = 0;
  if (status === "processing") activeIndex = 2;
  if (status === "completed") activeIndex = 3;
  if (status === "failed") activeIndex = 3; // conceptually it stops here

  return (
    <div className={cn("space-y-4", className)}>
      <h4 className="text-sm font-semibold text-slate-900">Resume Status</h4>
      <div className="flex flex-col gap-3">
        {steps.map((step, index) => {
          const isCompleted = index < activeIndex || (index === activeIndex && status === "completed");
          const isCurrent = index === activeIndex && status !== "completed" && status !== "failed";
          const isFailed = index === activeIndex && status === "failed";

          return (
            <div key={step.id} className="flex items-center gap-3">
              {isCompleted ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
              ) : isFailed ? (
                <CheckCircle2 className="h-5 w-5 text-red-500 shrink-0" />
              ) : isCurrent ? (
                <Clock className="h-5 w-5 text-indigo-500 shrink-0" />
              ) : (
                <Circle className="h-5 w-5 text-slate-300 shrink-0" />
              )}
              <span 
                className={cn(
                  "text-sm font-medium",
                  isCompleted || isCurrent ? "text-slate-900" : isFailed ? "text-red-600" : "text-slate-500"
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
