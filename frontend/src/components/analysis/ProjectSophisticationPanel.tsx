"use client";

import { useState } from "react";
import { BarChart3, TrendingUp, Award, ChevronRight, Info, Sparkles } from "lucide-react";
import StateWrapper from "./StateWrapper";
import {
  CandidateIntelligenceProfile,
  ProjectSophisticationRecord,
  SophisticationTier,
} from "@/types/candidate-profile";
import ProjectScoreReportModal from "./ProjectScoreReportModal";

interface ProjectSophisticationPanelProps {
  projectSophistication: ProjectSophisticationRecord[];
  averageProjectSophistication: number;
  highestProjectSophistication: number;
  isLoading?: boolean;
  error?: Error | null;
  profile?: CandidateIntelligenceProfile;
}

// ── Tier configuration ────────────────────────────────────────────────────

const TIER_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; bar: string }
> = {
  [SophisticationTier.BEGINNER]: {
    label: "Beginner",
    color: "text-slate-600",
    bg: "bg-slate-100",
    bar: "bg-slate-400",
  },
  [SophisticationTier.BASIC]: {
    label: "Basic",
    color: "text-sky-700",
    bg: "bg-sky-100",
    bar: "bg-sky-400",
  },
  [SophisticationTier.INTERMEDIATE]: {
    label: "Intermediate",
    color: "text-indigo-700",
    bg: "bg-indigo-100",
    bar: "bg-indigo-500",
  },
  [SophisticationTier.ADVANCED]: {
    label: "Advanced",
    color: "text-violet-700",
    bg: "bg-violet-100",
    bar: "bg-violet-500",
  },
  [SophisticationTier.NEAR_INDUSTRY_READY]: {
    label: "Near Industry Ready",
    color: "text-emerald-700",
    bg: "bg-emerald-100",
    bar: "bg-emerald-500",
  },
  [SophisticationTier.INDUSTRY_GRADE]: {
    label: "Industry Grade",
    color: "text-amber-700",
    bg: "bg-amber-100",
    bar: "bg-amber-500",
  },
};

const DEFAULT_TIER_CONFIG = {
  label: "Assessed",
  color: "text-slate-600",
  bg: "bg-slate-100",
  bar: "bg-slate-400",
};

function getTierConfig(tier: string) {
  return TIER_CONFIG[tier] ?? DEFAULT_TIER_CONFIG;
}

// ── Score color for the numeric label ────────────────────────────────────

function getScoreColor(score: number): string {
  if (score <= 20) return "text-slate-500";
  if (score <= 40) return "text-sky-600";
  if (score <= 60) return "text-indigo-600";
  if (score <= 80) return "text-violet-600";
  if (score <= 90) return "text-emerald-600";
  return "text-amber-600";
}

// ── Sub-components ────────────────────────────────────────────────────────

function AggregateMetricCard({
  icon,
  label,
  value,
  subtitle,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtitle: string;
}) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="mt-0.5 rounded-lg bg-white p-2 shadow-xs border border-slate-100">
        {icon}
      </div>
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {label}
        </p>
        <p className="text-2xl font-bold text-slate-900 mt-0.5">{value}</p>
        <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
      </div>
    </div>
  );
}

function ProjectSophisticationCard({
  record,
  onSelect,
}: {
  record: ProjectSophisticationRecord;
  onSelect: () => void;
}) {
  const cfg = getTierConfig(record.sophistication_tier);
  const scoreColor = getScoreColor(record.sophistication_score);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
      className="group rounded-xl border border-slate-200 bg-white p-5 shadow-xs hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer flex flex-col justify-between text-left focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 relative"
    >
      <div>
        {/* Header row */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div className="min-w-0 pr-1">
            <h5 className="font-semibold text-slate-900 truncate text-sm leading-snug group-hover:text-indigo-600 transition-colors">
              {record.project_name}
            </h5>
          </div>
          <span
            className={`shrink-0 inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold tracking-wide ${cfg.bg} ${cfg.color}`}
          >
            {cfg.label}
          </span>
        </div>

        {/* Progress bar + score */}
        <div className="flex items-center gap-3 mb-3">
          <div className="flex-1 h-2.5 rounded-full bg-slate-100 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${cfg.bar}`}
              style={{ width: `${record.sophistication_score}%` }}
            />
          </div>
          <span className={`text-lg font-bold tabular-nums w-10 text-right ${scoreColor}`}>
            {record.sophistication_score}
          </span>
          <span className="text-xs text-slate-400 font-medium">/ 100</span>
        </div>

        {/* Reasoning */}
        {record.sophistication_reasoning && (
          <p className="text-xs text-slate-500 leading-relaxed border-t border-slate-100 pt-2.5 mt-1 line-clamp-2">
            {record.sophistication_reasoning}
          </p>
        )}
      </div>

      {/* Click for Dimension Score Breakdown prompt */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-indigo-600 transition-colors">
        <span className="flex items-center gap-1 font-medium">
          <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
          Dimension Score Breakdown
        </span>
        <ChevronRight className="h-3.5 w-3.5 transform group-hover:translate-x-0.5 transition-transform" />
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────

export default function ProjectSophisticationPanel({
  projectSophistication,
  averageProjectSophistication,
  highestProjectSophistication,
  isLoading = false,
  error = null,
  profile,
}: ProjectSophisticationPanelProps) {
  const [selectedRecord, setSelectedRecord] = useState<ProjectSophisticationRecord | null>(null);

  const hasData = projectSophistication && projectSophistication.length > 0;

  // Sort by score descending for display
  const sorted = hasData
    ? [...projectSophistication].sort(
      (a, b) => b.sophistication_score - a.sophistication_score
    )
    : [];

  const topRecord = sorted[0];

  return (
    <StateWrapper
      isLoading={isLoading}
      error={error}
      isEmpty={!hasData}
      emptyTitle="No Sophistication Data"
      emptyMessage="Project sophistication scores will appear after resume analysis completes."
    >
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
        {/* Panel header */}
        <div className="mb-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-indigo-600" />
              Project Sophistication
            </h3>
            <p className="text-sm text-slate-500 mt-0.5">
              Holistic engineering maturity score per project (0–100). Click any project card to view its
              Dimension-by-Dimension Score Breakdown.
            </p>
          </div>
          <span className="inline-flex items-center gap-1.5 text-xs text-indigo-700 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-200 self-start sm:self-auto font-medium">
            <Info className="h-3.5 w-3.5" />
            Click card for Dimension Breakdown
          </span>
        </div>

        {/* Aggregate metrics row */}
        {hasData && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
            <AggregateMetricCard
              icon={<TrendingUp className="h-4 w-4 text-indigo-500" />}
              label="Average Score"
              value={averageProjectSophistication.toFixed(1)}
              subtitle={`across ${projectSophistication.length} project${projectSophistication.length !== 1 ? "s" : ""}`}
            />
            <AggregateMetricCard
              icon={<Award className="h-4 w-4 text-amber-500" />}
              label="Highest Score"
              value={String(highestProjectSophistication)}
              subtitle={topRecord ? getTierConfig(topRecord.sophistication_tier).label : ""}
            />
          </div>
        )}

        {/* Per-project cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {sorted.map((record, idx) => (
            <ProjectSophisticationCard
              key={idx}
              record={record}
              onSelect={() => setSelectedRecord(record)}
            />
          ))}
        </div>
      </div>

      {/* Detailed Dimension-by-Dimension Calculation Report Modal */}
      <ProjectScoreReportModal
        isOpen={!!selectedRecord}
        onClose={() => setSelectedRecord(null)}
        record={selectedRecord}
        profile={profile}
      />
    </StateWrapper>
  );
}
