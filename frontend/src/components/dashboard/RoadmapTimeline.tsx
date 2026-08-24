"use client";

/**
 * components/dashboard/RoadmapTimeline.tsx
 * -----------------------------------------
 * Project phase roadmap timeline matching the actual SkillFit roadmap
 * from internal_docs/development-roadmap.md.
 *
 * Only 3 phases are shown as they are the only ones currently defined.
 */

import { motion } from "framer-motion";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

type PhaseStatus = "complete" | "in-progress" | "upcoming";

interface Phase {
  number: number;
  name: string;
  description: string;
  status: PhaseStatus;
}

const PHASES: Phase[] = [
  {
    number: 1,
    name: "Database Foundation",
    description: "PostgreSQL schema, ORM models, relationships, migrations",
    status: "complete",
  },
  {
    number: 2,
    name: "Authentication, Authorization & Security",
    description: "JWT auth, registration, login, RBAC, rate limiting, password hashing",
    status: "complete",
  },
  {
    number: 3,
    name: "Resume Intelligence & AI Features",
    description: "Resume upload & parsing, skill extraction, LLM integration, readiness engine",
    status: "in-progress",
  },
];

function PhaseIcon({ status }: { status: PhaseStatus }) {
  if (status === "complete")
    return <CheckCircle2 className="h-5 w-5 text-emerald-500" aria-hidden="true" />;
  if (status === "in-progress")
    return <Loader2 className="h-5 w-5 animate-spin text-indigo-500" aria-hidden="true" />;
  return <Circle className="h-5 w-5 text-slate-300" aria-hidden="true" />;
}

const statusLabel: Record<PhaseStatus, { text: string; className: string }> = {
  complete: { text: "Complete", className: "bg-emerald-50 text-emerald-700" },
  "in-progress": { text: "In Progress", className: "bg-indigo-50 text-indigo-700" },
  upcoming: { text: "Planned", className: "bg-slate-100 text-slate-500" },
};

export default function RoadmapTimeline() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.15 }}
      className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
    >
      <h3 className="mb-5 text-sm font-semibold text-slate-900">Project Roadmap</h3>

      <ol className="relative space-y-0" aria-label="SkillFit project phases">
        {PHASES.map((phase, index) => (
          <li key={phase.number} className="relative flex gap-4">
            {/* Vertical connector line */}
            {index < PHASES.length - 1 && (
              <div
                aria-hidden="true"
                className="absolute left-2.5 top-8 h-full w-px bg-slate-100"
              />
            )}

            {/* Icon */}
            <div className="relative z-10 mt-0.5 shrink-0">
              <PhaseIcon status={phase.status} />
            </div>

            {/* Content */}
            <div className="pb-6 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="text-sm font-medium text-slate-900">
                  Phase {phase.number} — {phase.name}
                </span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusLabel[phase.status].className}`}
                >
                  {statusLabel[phase.status].text}
                </span>
              </div>
              <p className="text-xs leading-relaxed text-slate-500">{phase.description}</p>
            </div>
          </li>
        ))}
      </ol>
    </motion.div>
  );
}
