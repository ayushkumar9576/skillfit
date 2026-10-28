"use client";

import React from "react";
import { 
  X, 
  Code2, 
  BrainCircuit, 
  Globe2, 
  Zap, 
  FolderGit2, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  Sparkles,
  Info
} from "lucide-react";
import { DimensionBreakdown } from "@/lib/api/matching";

interface DetailedScoreBreakdownModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  score: number;
  rawScore?: number;
  tier: string;
  narrative: string;
  dimensionBreakdown?: DimensionBreakdown[];
  strengths: string[];
  gaps: string[];
}

const DIMENSION_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }>; color: string; bg: string; border: string }> = {
  TECHNOLOGY: {
    label: "Technologies & Tools",
    icon: Code2,
    color: "text-blue-600",
    bg: "bg-blue-50",
    border: "border-blue-200"
  },
  COMPETENCY: {
    label: "Core Engineering Competencies",
    icon: BrainCircuit,
    color: "text-purple-600",
    bg: "bg-purple-50",
    border: "border-purple-200"
  },
  DOMAIN: {
    label: "Domain Alignment",
    icon: Globe2,
    color: "text-teal-600",
    bg: "bg-teal-50",
    border: "border-teal-200"
  },
  SIGNAL: {
    label: "Hiring Signals & Success Indicators",
    icon: Zap,
    color: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-200"
  },
  PROJECT: {
    label: "Project Sophistication",
    icon: FolderGit2,
    color: "text-indigo-600",
    bg: "bg-indigo-50",
    border: "border-indigo-200"
  },
  BEHAVIORAL: {
    label: "Ownership & Engineering Practices",
    icon: ShieldCheck,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
    border: "border-emerald-200"
  }
};

export default function DetailedScoreBreakdownModal({
  isOpen,
  onClose,
  title,
  subtitle,
  score,
  rawScore,
  tier,
  narrative,
  dimensionBreakdown = [],
  strengths,
  gaps
}: DetailedScoreBreakdownModalProps) {
  if (!isOpen) return null;

  const matchPercentage = Math.round(score * 100);
  const cleanTier = tier.replace("_MATCH", "");

  const tierColors = {
    EXCELLENT: "bg-emerald-100 text-emerald-800 border-emerald-300",
    STRONG: "bg-indigo-100 text-indigo-800 border-indigo-300",
    MODERATE: "bg-amber-100 text-amber-800 border-amber-300",
    PARTIAL: "bg-orange-100 text-orange-800 border-orange-300",
    WEAK: "bg-rose-100 text-rose-800 border-rose-300"
  }[cleanTier] || "bg-slate-100 text-slate-800 border-slate-300";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div 
        className="bg-white rounded-3xl shadow-2xl w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200 border border-slate-100"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-6 sm:p-7 border-b border-slate-100 bg-gradient-to-r from-slate-50 via-white to-indigo-50/30 flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-wider border ${tierColors}`}>
                {cleanTier} MATCH
              </span>
              <span className="text-2xl font-black text-slate-900 tracking-tight">
                {matchPercentage}%
              </span>
              {rawScore !== undefined && (
                <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Morale Boost Calibrated
                </span>
              )}
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
              {title}
            </h2>
            {subtitle && (
              <p className="text-sm font-medium text-slate-500">
                {subtitle}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors"
            title="Close modal"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 sm:p-8 space-y-7 overflow-y-auto">
          {/* Executive Narrative */}
          <div className="bg-indigo-50/70 border border-indigo-100 p-4 sm:p-5 rounded-2xl flex items-start gap-3.5">
            <Sparkles className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-900">
                Match Intelligence Summary
              </h4>
              <p className="text-sm text-slate-700 leading-relaxed font-normal">
                {narrative || "Candidate and drive alignment computed based on semantic vector comparison and evidence verification."}
              </p>
            </div>
          </div>

          {/* Dimension Breakdown Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Info className="w-4 h-4 text-slate-500" />
                Dimension-by-Dimension Score Breakdown
              </h3>
              <span className="text-xs text-slate-500 font-medium">
                Normalized to 100% total contribution
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dimensionBreakdown.length > 0 ? (
                dimensionBreakdown.map((dim) => {
                  const config = DIMENSION_CONFIG[dim.dimension] || {
                    label: dim.dimension,
                    icon: Info,
                    color: "text-slate-600",
                    bg: "bg-slate-50",
                    border: "border-slate-200"
                  };
                  const IconComponent = config.icon;
                  const rawPercent = Math.round(dim.raw_score * 100);
                  const contributionPercent = (dim.weighted_score * 100).toFixed(1);
                  const weightPercent = Math.round(dim.weight * 100);

                  return (
                    <div 
                      key={dim.dimension} 
                      className={`p-4 rounded-2xl border ${config.border} bg-white shadow-xs hover:shadow-sm transition-all flex flex-col justify-between`}
                    >
                      <div className="space-y-2">
                        {/* Title & Icon */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className={`p-1.5 rounded-lg ${config.bg} ${config.color}`}>
                              <IconComponent className="w-4 h-4" />
                            </div>
                            <span className="text-sm font-bold text-slate-900">
                              {config.label}
                            </span>
                          </div>
                          <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                            Weight: {weightPercent}%
                          </span>
                        </div>

                        {/* Progress Bar & Scores */}
                        <div className="space-y-1.5 pt-1">
                          <div className="flex justify-between items-baseline text-xs">
                            <span className="font-semibold text-slate-700">
                              Alignment: {rawPercent}%
                            </span>
                            <span className="font-bold text-indigo-700">
                              +{contributionPercent}% to score
                            </span>
                          </div>
                          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div 
                              className={`h-2 rounded-full transition-all duration-500 ${
                                rawPercent >= 75 ? "bg-emerald-500" :
                                rawPercent >= 50 ? "bg-indigo-500" :
                                rawPercent >= 30 ? "bg-amber-500" : "bg-rose-400"
                              }`}
                              style={{ width: `${Math.max(4, rawPercent)}%` }}
                            />
                          </div>
                        </div>

                        {/* Reasoning */}
                        <p className="text-xs text-slate-600 pt-1 leading-normal">
                          {dim.reasoning}
                        </p>
                      </div>

                      {/* Items coverage badge if applicable */}
                      {dim.total_items > 0 && (
                        <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                          <span>Coverage</span>
                          <span className="font-semibold text-slate-800">
                            {dim.matched_items} of {dim.total_items} items matched
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div className="col-span-2 text-center py-6 text-sm text-slate-400">
                  Detailed dimension data will display upon drive analysis completion.
                </div>
              )}
            </div>
          </div>

          {/* Strengths & Gaps Comparison Column */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-2">
            {/* Strengths Card */}
            <div className="bg-emerald-50/50 border border-emerald-100/80 rounded-2xl p-5 space-y-3">
              <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Verified Strengths (Matched Requirements)</span>
              </div>
              <ul className="space-y-2">
                {strengths && strengths.length > 0 ? (
                  strengths.map((str, idx) => (
                    <li key={idx} className="flex items-start text-xs text-slate-800 font-medium">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 mr-2 shrink-0" />
                      <span>{str}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-xs text-slate-400 italic">No prominent strengths identified.</li>
                )}
              </ul>
            </div>

            {/* Gaps Card */}
            <div className="bg-rose-50/50 border border-rose-100/80 rounded-2xl p-5 space-y-3">
              <div className="flex items-center gap-2 text-rose-800 font-bold text-sm">
                <XCircle className="w-4 h-4 text-rose-600" />
                <span>Key Missing Requirements (Gaps)</span>
              </div>
              <ul className="space-y-2">
                {gaps && gaps.length > 0 ? (
                  gaps.map((gap, idx) => (
                    <li key={idx} className="flex items-start text-xs text-slate-800 font-medium">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 mr-2 shrink-0" />
                      <span>{gap}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-xs text-emerald-700 italic font-medium">Candidate satisfies all evaluated requirements.</li>
                )}
              </ul>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 sm:p-5 bg-slate-50 border-t border-slate-100 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 text-sm font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 hover:border-slate-300 transition-all shadow-xs cursor-pointer"
          >
            Close Breakdown
          </button>
        </div>
      </div>
    </div>
  );
}
