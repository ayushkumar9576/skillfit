"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

const stages = [
  "Analysis Started",
  "Processing Drive Context",
  "Generating Intelligence",
  "Building Intelligence Profile",
  "Finalizing Results",
];

export default function AnalysisWorkflowTracker() {
  const [currentStage, setCurrentStage] = useState(0);

  // This is a purely visual simulation for user feedback.
  // The backend does not expose granular progress.
  useEffect(() => {
    if (currentStage >= stages.length - 1) return;

    const timer = setTimeout(() => {
      setCurrentStage((prev) => prev + 1);
    }, 4000); // Progress every 4 seconds visually

    return () => clearTimeout(timer);
  }, [currentStage]);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
          <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" />
          Analysis in Progress
        </h3>
        <p className="text-sm text-slate-500 mt-1">
          Our intelligence engine is currently analyzing the drive context. This may take a few moments.
          The timeline below is a visual indicator of background activity.
        </p>
      </div>

      <div className="space-y-4 relative before:absolute before:inset-0 before:ml-[11px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-200 before:to-transparent">
        {stages.map((stage, index) => {
          const isCompleted = index < currentStage;
          const isCurrent = index === currentStage;

          return (
            <div key={stage} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
              {/* Icon marker */}
              <div
                className={`flex items-center justify-center w-6 h-6 rounded-full border-2 bg-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm z-10 ${
                  isCompleted
                    ? "border-emerald-500 text-emerald-500"
                    : isCurrent
                    ? "border-indigo-500 text-indigo-500"
                    : "border-slate-300 text-slate-300"
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : isCurrent ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Circle className="w-3.5 h-3.5 fill-slate-100" />
                )}
              </div>

              {/* Content box */}
              <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-slate-200 bg-white shadow-sm flex flex-col gap-1">
                <span className={`text-sm font-medium ${isCurrent ? "text-indigo-900" : isCompleted ? "text-slate-700" : "text-slate-400"}`}>
                  {stage}
                </span>
                {isCurrent && (
                  <span className="text-xs text-indigo-500 animate-pulse">Running...</span>
                )}
                {isCompleted && (
                  <span className="text-xs text-emerald-500">Completed</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
