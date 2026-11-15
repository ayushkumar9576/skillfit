"use client";

import React, { useEffect, useMemo } from "react";
import {
  X,
  Code2,
  BrainCircuit,
  Server,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Sparkles,
  Info,
  AlertTriangle,
  Zap,
  Layers,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import {
  CandidateIntelligenceProfile,
  EngineeringSignalCategory,
  FindingType,
  OwnershipLevel,
  ProjectSophisticationRecord,
  SophisticationTier,
} from "@/types/candidate-profile";

interface ProjectScoreReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  record: ProjectSophisticationRecord | null;
  profile?: CandidateIntelligenceProfile;
}

interface ProjectDimension {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bg: string;
  border: string;
  weight: number; // 0.0 to 1.0
  raw_score: number; // 0.0 to 1.0
  weighted_score: number; // raw_score * weight
  reasoning: string;
  matched_items: number;
  total_items: number;
}

export default function ProjectScoreReportModal({
  isOpen,
  onClose,
  record,
  profile,
}: ProjectScoreReportModalProps) {
  // Close on ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  const projectName = record?.project_name ?? "";
  const score = record?.sophistication_score ?? 0;
  const tier = record?.sophistication_tier ?? SophisticationTier.BEGINNER;

  // Filter project-specific intelligence signals from candidate profile
  const projectData = useMemo(() => {
    if (!profile || !projectName) {
      return {
        technologies: [],
        competencies: [],
        engineeringSignals: [],
        ownershipSignals: [],
        findings: [],
        quotes: [],
      };
    }

    const normTarget = projectName.toLowerCase().trim();
    const hasSingleProject = (profile.project_sophistication?.length || 0) <= 1;

    const matchesProject = (evidenceList?: { source?: string; source_id?: string }[]) => {
      if (!evidenceList || evidenceList.length === 0) {
        return hasSingleProject;
      }
      return evidenceList.some((ev) => {
        const sid = ev.source_id?.toLowerCase().trim();
        if (!sid) return hasSingleProject && ev.source === "project";
        return sid === normTarget || normTarget.includes(sid) || sid.includes(normTarget);
      });
    };

    const technologies = (profile.technologies || []).filter((t) => matchesProject(t.evidence));

    const competencies = (profile.competencies || []).filter((c) => {
      const matchProjects = (c.supporting_projects || []).some((p) => {
        const normP = p.toLowerCase().trim();
        return normP === normTarget || normTarget.includes(normP) || normP.includes(normTarget);
      });
      return matchProjects || matchesProject(c.evidence);
    });

    const engineeringSignals = (profile.engineering_signals || []).filter((e) =>
      matchesProject(e.evidence)
    );

    const ownershipSignals = (profile.ownership_signals || []).filter((o) =>
      matchesProject(o.evidence)
    );

    const findings = (profile.findings || []).filter((f) => {
      const titleMatches = f.title?.toLowerCase().includes(normTarget);
      const descMatches = f.description?.toLowerCase().includes(normTarget);
      return titleMatches || descMatches || matchesProject(f.evidence);
    });

    // Collect quotes
    const quoteSet = new Set<string>();
    const quotesList: { quote: string; line?: number | null }[] = [];
    const collectQuotes = (evidenceList?: { quote?: string; line_reference?: number | null }[]) => {
      evidenceList?.forEach((ev) => {
        if (ev.quote && !quoteSet.has(ev.quote)) {
          quoteSet.add(ev.quote);
          quotesList.push({ quote: ev.quote, line: ev.line_reference });
        }
      });
    };

    technologies.forEach((t) => collectQuotes(t.evidence));
    competencies.forEach((c) => collectQuotes(c.evidence));
    engineeringSignals.forEach((e) => collectQuotes(e.evidence));
    ownershipSignals.forEach((o) => collectQuotes(o.evidence));
    findings.forEach((f) => collectQuotes(f.evidence));

    return {
      technologies,
      competencies,
      engineeringSignals,
      ownershipSignals,
      findings,
      quotes: quotesList,
    };
  }, [profile, projectName]);

  // Build the 6 Dimension-by-Dimension breakdown objects
  const { dimensions, strengths, gaps } = useMemo(() => {
    if (!record) {
      return { dimensions: [], strengths: [], gaps: [] };
    }

    const engSignals = projectData.engineeringSignals;
    const ownSignals = projectData.ownershipSignals;
    const techs = projectData.technologies;
    const comps = projectData.competencies;
    const totalScoreNorm = Math.max(0, Math.min(100, score)) / 100;

    // 1. System Architecture & Design (Weight: 20%)
    const archSignals = engSignals.filter(
      (e) => e.category === EngineeringSignalCategory.ARCHITECTURE && e.demonstrated
    );
    const hasArch = archSignals.length > 0;
    const archRaw = hasArch
      ? Math.max(0.75, Math.min(0.95, totalScoreNorm * 1.1))
      : Math.max(0.1, Math.min(0.35, totalScoreNorm * 0.6));
    const archReason = hasArch
      ? `Demonstrated architectural design (${archSignals[0]?.signal || "modular structure evidenced"}).`
      : "Single-module or simple script structure; lacks clear API boundaries, layered architecture, or service contracts.";

    // 2. Deployment & Cloud Infrastructure (Weight: 20%)
    const depSignals = engSignals.filter(
      (e) => e.category === EngineeringSignalCategory.DEPLOYMENT && e.demonstrated
    );
    const hasDep = depSignals.length > 0;
    const depRaw = hasDep
      ? Math.max(0.8, Math.min(0.95, totalScoreNorm * 1.15))
      : Math.max(0.05, Math.min(0.25, totalScoreNorm * 0.4));
    const depReason = hasDep
      ? `Verified production deployment practices (${depSignals[0]?.signal || "container/cloud deployment"}).`
      : "No Docker containerization, Kubernetes, CI/CD pipeline, or cloud hosting (AWS/GCP/Vercel) evidenced.";

    // 3. Automated Testing & Code Quality (Weight: 15%)
    const testSignals = engSignals.filter(
      (e) => e.category === EngineeringSignalCategory.TESTING && e.demonstrated
    );
    const hasTest = testSignals.length > 0;
    const testRaw = hasTest
      ? Math.max(0.8, Math.min(0.95, totalScoreNorm * 1.15))
      : Math.max(0.05, Math.min(0.2, totalScoreNorm * 0.35));
    const testReason = hasTest
      ? `Automated testing and QA coverage evidenced (${testSignals[0]?.signal || "unit/integration tests"}).`
      : "Missing automated unit testing, pytest/Jest test suites, or test coverage verification.";

    // 4. Security & Authentication (Weight: 15%)
    const secSignals = engSignals.filter(
      (e) => e.category === EngineeringSignalCategory.SECURITY && e.demonstrated
    );
    const hasSec = secSignals.length > 0;
    const secRaw = hasSec
      ? Math.max(0.75, Math.min(0.95, totalScoreNorm * 1.1))
      : Math.max(0.1, Math.min(0.3, totalScoreNorm * 0.5));
    const secReason = hasSec
      ? `Security and authentication controls detected (${secSignals[0]?.signal || "secure auth/storage"}).`
      : "No OAuth, JWT authentication, data encryption, or input validation mechanisms documented.";

    // 5. Ownership & Leadership Depth (Weight: 15%)
    const highestOwnership = ownSignals.reduce<string | null>((highest, curr) => {
      const order = [
        OwnershipLevel.OBSERVED,
        OwnershipLevel.CONTRIBUTED,
        OwnershipLevel.IMPLEMENTED,
        OwnershipLevel.OWNED,
        OwnershipLevel.LED,
      ];
      const currIdx = order.indexOf(curr.ownership_level as OwnershipLevel);
      const highestIdx = highest ? order.indexOf(highest as OwnershipLevel) : -1;
      return currIdx > highestIdx ? curr.ownership_level : highest;
    }, null);

    let ownRaw = 0.2;
    if (highestOwnership === OwnershipLevel.LED) ownRaw = 0.95;
    else if (highestOwnership === OwnershipLevel.OWNED) ownRaw = 0.85;
    else if (highestOwnership === OwnershipLevel.IMPLEMENTED) ownRaw = 0.65;
    else if (highestOwnership === OwnershipLevel.CONTRIBUTED) ownRaw = 0.4;
    else ownRaw = Math.max(0.15, Math.min(0.5, totalScoreNorm * 0.7));

    const ownReason = highestOwnership
      ? `Demonstrated ${highestOwnership} level individual ownership and technical contribution.`
      : "Passive bullet phrasing ('used', 'assisted', 'contributed'); lacks strong ownership verbs ('architected', 'spearheaded').";

    // 6. Technical Stack Breadth & Competency (Weight: 15%)
    const techCount = techs.length;
    let techRaw = 0.3;
    if (techCount >= 4) techRaw = 0.9;
    else if (techCount >= 3) techRaw = 0.75;
    else if (techCount >= 2) techRaw = 0.6;
    else techRaw = Math.max(0.2, Math.min(0.5, totalScoreNorm * 0.8));

    const techReason =
      techCount >= 3
        ? `Multi-tier stack evidenced across ${techCount} verified technologies and tools.`
        : `${techCount || 1} technology identified; stack breadth is limited to a single layer.`;

    const dims: ProjectDimension[] = [
      {
        id: "ARCHITECTURE",
        label: "System Architecture & Design",
        icon: Layers,
        color: "text-purple-600",
        bg: "bg-purple-50",
        border: "border-purple-200",
        weight: 0.2,
        raw_score: archRaw,
        weighted_score: archRaw * 0.2,
        reasoning: archReason,
        matched_items: hasArch ? archSignals.length : 0,
        total_items: Math.max(1, archSignals.length),
      },
      {
        id: "DEPLOYMENT",
        label: "Deployment & Cloud Infrastructure",
        icon: Server,
        color: "text-indigo-600",
        bg: "bg-indigo-50",
        border: "border-indigo-200",
        weight: 0.2,
        raw_score: depRaw,
        weighted_score: depRaw * 0.2,
        reasoning: depReason,
        matched_items: hasDep ? depSignals.length : 0,
        total_items: Math.max(1, depSignals.length),
      },
      {
        id: "TESTING",
        label: "Automated Testing & QA",
        icon: ShieldCheck,
        color: "text-emerald-600",
        bg: "bg-emerald-50",
        border: "border-emerald-200",
        weight: 0.15,
        raw_score: testRaw,
        weighted_score: testRaw * 0.15,
        reasoning: testReason,
        matched_items: hasTest ? testSignals.length : 0,
        total_items: Math.max(1, testSignals.length),
      },
      {
        id: "SECURITY",
        label: "Security & Authentication",
        icon: Zap,
        color: "text-amber-600",
        bg: "bg-amber-50",
        border: "border-amber-200",
        weight: 0.15,
        raw_score: secRaw,
        weighted_score: secRaw * 0.15,
        reasoning: secReason,
        matched_items: hasSec ? secSignals.length : 0,
        total_items: Math.max(1, secSignals.length),
      },
      {
        id: "OWNERSHIP",
        label: "Ownership & Leadership Depth",
        icon: BrainCircuit,
        color: "text-blue-600",
        bg: "bg-blue-50",
        border: "border-blue-200",
        weight: 0.15,
        raw_score: ownRaw,
        weighted_score: ownRaw * 0.15,
        reasoning: ownReason,
        matched_items: highestOwnership ? 1 : 0,
        total_items: 1,
      },
      {
        id: "TECHNOLOGY",
        label: "Technical Stack & Breadth",
        icon: Code2,
        color: "text-teal-600",
        bg: "bg-teal-50",
        border: "border-teal-200",
        weight: 0.15,
        raw_score: techRaw,
        weighted_score: techRaw * 0.15,
        reasoning: techReason,
        matched_items: techCount,
        total_items: Math.max(3, techCount),
      },
    ];

    // Compute Strengths and Gaps lists
    const strList: string[] = [];
    const gapList: string[] = [];

    if (hasArch) strList.push("Demonstrated structured system architecture and design patterns.");
    else gapList.push("Lacks system architecture complexity (no API contracts, layered design, or caching patterns).");

    if (hasDep) strList.push("Verified deployment practices (Docker, cloud hosting, or CI/CD).");
    else gapList.push("Missing production deployment signal (no Docker, Kubernetes, AWS/GCP, or CI/CD pipelines).");

    if (hasTest) strList.push("Automated testing and QA coverage evidenced in project execution.");
    else gapList.push("No automated unit or integration tests (pytest/Jest/JUnit) evidenced in resume bullets.");

    if (hasSec) strList.push("Integrated security, authentication, or access controls.");
    else gapList.push("No authentication, authorization, or secure data handling mechanisms documented.");

    if (highestOwnership === OwnershipLevel.LED || highestOwnership === OwnershipLevel.OWNED) {
      strList.push(`Strong individual ownership demonstrated (${highestOwnership} level).`);
    } else {
      gapList.push("Passive ownership phrasing; bullets rely on 'used' or 'contributed' rather than assertive ownership verbs.");
    }

    if (techCount >= 3) {
      strList.push(`Multi-tier technology stack verified with ${techCount} distinct technologies.`);
    } else {
      gapList.push("Single-tier technology stack; does not demonstrate full-stack or multi-component integration.");
    }

    // Add findings from profile if available
    projectData.findings.forEach((f) => {
      if (f.type === FindingType.STRENGTH) {
        strList.push(`${f.title}: ${f.description}`);
      } else if (f.type === FindingType.WEAKNESS || f.type === FindingType.MISSING_SIGNAL) {
        gapList.push(`${f.title}: ${f.description}`);
      }
    });

    return { dimensions: dims, strengths: strList, gaps: gapList };
  }, [record, projectData, score]);

  if (!isOpen || !record) return null;

  const cleanTier = tier.replace("_GRADE", "").replace("_READY", "");

  const tierColors: Record<string, string> = {
    INDUSTRY: "bg-amber-100 text-amber-800 border-amber-300",
    NEAR_INDUSTRY: "bg-emerald-100 text-emerald-800 border-emerald-300",
    ADVANCED: "bg-violet-100 text-violet-800 border-violet-300",
    INTERMEDIATE: "bg-indigo-100 text-indigo-800 border-indigo-300",
    BASIC: "bg-sky-100 text-sky-800 border-sky-300",
    BEGINNER: "bg-slate-100 text-slate-800 border-slate-300",
  };
  const tierBadgeColor = tierColors[cleanTier] || "bg-slate-100 text-slate-800 border-slate-300";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 backdrop-blur-sm overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-3xl shadow-2xl w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200 border border-slate-100"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-6 sm:p-7 border-b border-slate-100 bg-gradient-to-r from-slate-50 via-white to-indigo-50/30 flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold tracking-wider border ${tierBadgeColor}`}
              >
                {tier.replace(/_/g, " ")} TIER
              </span>
              <span className="text-2xl font-black text-slate-900 tracking-tight">
                {score} / 100
              </span>
              {score <= 40 ? (
                <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Academic / Introductory Scope
                </span>
              ) : score <= 60 ? (
                <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
                  Moderate Engineering Depth
                </span>
              ) : (
                <span className="text-xs font-medium px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  High Production Maturity
                </span>
              )}
            </div>

            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
              {projectName}
            </h2>
            <p className="text-sm font-medium text-slate-500">
              Project Sophistication Assessment &amp; Scoring Breakdown
            </p>
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
          {/* Executive Narrative / AI Reasoning */}
          <div className="bg-indigo-50/70 border border-indigo-100 p-4 sm:p-5 rounded-2xl flex items-start gap-3.5">
            <Sparkles className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-900">
                Project Evaluation Summary
              </h4>
              <p className="text-sm text-slate-700 leading-relaxed font-normal">
                {record.sophistication_reasoning ||
                  "The project sophistication score evaluates technical breadth, architectural complexity, testing discipline, and deployment maturity extracted from your resume."}
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
              {dimensions.map((dim) => {
                const IconComponent = dim.icon;
                const rawPercent = Math.round(dim.raw_score * 100);
                const contributionPercent = (dim.weighted_score * 100).toFixed(1);
                const weightPercent = Math.round(dim.weight * 100);

                return (
                  <div
                    key={dim.id}
                    className={`p-4 rounded-2xl border ${dim.border} bg-white shadow-xs hover:shadow-sm transition-all flex flex-col justify-between`}
                  >
                    <div className="space-y-2">
                      {/* Title & Icon & Weight pill */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`p-1.5 rounded-lg ${dim.bg} ${dim.color}`}>
                            <IconComponent className="w-4 h-4" />
                          </div>
                          <span className="text-sm font-bold text-slate-900">
                            {dim.label}
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
                            +{contributionPercent} pts to score
                          </span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${rawPercent >= 75
                              ? "bg-emerald-500"
                              : rawPercent >= 50
                                ? "bg-indigo-500"
                                : rawPercent >= 30
                                  ? "bg-amber-500"
                                  : "bg-rose-400"
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

                    {/* Items coverage badge */}
                    {dim.total_items > 0 && (
                      <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                        <span>Coverage</span>
                        <span className="font-semibold text-slate-800">
                          {dim.matched_items} of {dim.total_items} signals verified
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Strengths & Gaps Comparison Column */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-2">
            {/* Strengths Card */}
            <div className="bg-emerald-50/50 border border-emerald-100/80 rounded-2xl p-5 space-y-3">
              <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Verified Strengths (Demonstrated Practices)</span>
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
                  <li className="text-xs text-slate-400 italic">
                    No prominent advanced practices detected.
                  </li>
                )}
              </ul>
            </div>

            {/* Gaps Card (Why is the score low?) */}
            <div className="bg-rose-50/50 border border-rose-100/80 rounded-2xl p-5 space-y-3">
              <div className="flex items-center gap-2 text-rose-800 font-bold text-sm">
                <XCircle className="w-4 h-4 text-rose-600" />
                <span>Key Missing Signals (Why Score Is Low)</span>
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
                  <li className="text-xs text-emerald-700 italic font-medium">
                    Candidate satisfies all evaluated engineering dimensions.
                  </li>
                )}
              </ul>
            </div>
          </div>

          {/* Actionable Advice to Boost Score */}
          <div className="rounded-2xl border border-indigo-100 bg-gradient-to-r from-slate-50 via-white to-indigo-50/20 p-5 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-900 flex items-center gap-2">
              <ArrowRight className="w-4 h-4 text-indigo-600" />
              How to Raise This Score on Your Resume
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-600">
              <div className="p-3 bg-white rounded-xl border border-slate-100">
                <span className="font-bold text-slate-800 block mb-1">
                  1. Add Automated Testing Evidence
                </span>
                Specify unit/integration test tools: e.g. &ldquo;Authored 25+ pytest test cases ensuring 85% coverage.&rdquo;
              </div>
              <div className="p-3 bg-white rounded-xl border border-slate-100">
                <span className="font-bold text-slate-800 block mb-1">
                  2. Document Containerization &amp; Cloud
                </span>
                Highlight infrastructure: e.g. &ldquo;Containerized with Docker; deployed automated CI/CD pipeline on AWS.&rdquo;
              </div>
              <div className="p-3 bg-white rounded-xl border border-slate-100">
                <span className="font-bold text-slate-800 block mb-1">
                  3. Highlight Architectural Complexity
                </span>
                Mention caching (Redis), API contracts, rate limiting, indexing, or async queues.
              </div>
              <div className="p-3 bg-white rounded-xl border border-slate-100">
                <span className="font-bold text-slate-800 block mb-1">
                  4. Use Assertive Ownership Verbs
                </span>
                Replace &ldquo;Assisted&rdquo; or &ldquo;Used&rdquo; with &ldquo;Architected&rdquo;, &ldquo;Engineered&rdquo;, &ldquo;Designed&rdquo;, &ldquo;Spearheaded&rdquo;.
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 sm:p-5 bg-slate-50 border-t border-slate-100 flex flex-wrap items-center justify-end gap-3">
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

