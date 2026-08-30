import { BarChart3, TrendingUp, Award } from "lucide-react";
import StateWrapper from "./StateWrapper";
import {
  ProjectSophisticationRecord,
  SophisticationTier,
} from "@/types/candidate-profile";

interface ProjectSophisticationPanelProps {
  projectSophistication: ProjectSophisticationRecord[];
  averageProjectSophistication: number;
  highestProjectSophistication: number;
  isLoading?: boolean;
  error?: Error | null;
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
      <div className="mt-0.5 rounded-lg bg-white p-2 shadow-sm border border-slate-100">
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
}: {
  record: ProjectSophisticationRecord;
}) {
  const cfg = getTierConfig(record.sophistication_tier);
  const scoreColor = getScoreColor(record.sophistication_score);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <h5 className="font-semibold text-slate-900 truncate text-sm leading-snug">
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
        <p className="text-xs text-slate-500 leading-relaxed border-t border-slate-100 pt-2.5 mt-1">
          {record.sophistication_reasoning}
        </p>
      )}
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
}: ProjectSophisticationPanelProps) {
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
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        {/* Panel header */}
        <div className="mb-5">
          <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-violet-500" />
            Project Sophistication
          </h3>
          <p className="text-sm text-slate-500 mt-1">
            Holistic engineering maturity score per project (0–100), derived from
            architecture, depth, integrations, and ownership signals.
          </p>
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
            <ProjectSophisticationCard key={idx} record={record} />
          ))}
        </div>
      </div>
    </StateWrapper>
  );
}
