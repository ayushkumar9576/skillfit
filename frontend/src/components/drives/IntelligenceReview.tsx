/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React from "react";
import { 
  CheckCircle2, 
  AlertTriangle, 
  Lightbulb, 
  User, 
  Code2, 
  ShieldAlert, 
  Sparkles, 
  Target, 
  BookOpen, 
  Layers, 
  Quote,
  GraduationCap
} from "lucide-react";
import {
  formatCompetency,
  formatBehavioralSkill,
  formatHiringSignal,
  formatRiskType,
  formatDifficultyLevel,
  formatImportance,
  formatRoundType,
} from "@/lib/mappers/drive-intelligence";

interface IntelligenceReviewProps {
  snapshot: any;
}

export default function IntelligenceReview({ snapshot }: IntelligenceReviewProps) {
  const payload = snapshot?.intelligence_payload || {};
  const technologies = Array.isArray(payload.technologies) ? payload.technologies : [];
  const techCompetencies = Array.isArray(payload.technical_competencies) ? payload.technical_competencies : [];
  const behaviors = Array.isArray(payload.behavioral_competencies) ? payload.behavioral_competencies : [];
  const signals = Array.isArray(payload.hiring_signals) ? payload.hiring_signals : [];
  const risks = Array.isArray(payload.risks) ? payload.risks : [];
  const expectations = Array.isArray(payload.role_expectations) ? payload.role_expectations : [];
  const qualifications = Array.isArray(payload.qualifications) ? payload.qualifications : [];
  const selectionRounds = Array.isArray(payload.selection_process) ? payload.selection_process : [];
  const difficulty = payload.difficulty;
  const placementRelevance = payload.placement_relevance;
  const preparation = payload.preparation;

  const renderImportanceBadge = (importance?: string) => {
    if (!importance) return null;
    const upper = String(importance).toUpperCase();
    if (upper === "CRITICAL") {
      return (
        <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-800 rounded border border-rose-200">
          Critical
        </span>
      );
    }
    if (upper === "HIGH") {
      return (
        <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-indigo-100 text-indigo-800 rounded border border-indigo-200">
          High
        </span>
      );
    }
    if (upper === "MEDIUM") {
      return (
        <span className="px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider bg-slate-100 text-slate-700 rounded border border-slate-200">
          Medium
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-[10px] font-normal uppercase tracking-wider bg-slate-50 text-slate-500 rounded border border-slate-200">
        Low
      </span>
    );
  };

  const renderSeverityBadge = (severity?: string) => {
    if (!severity) return null;
    const upper = String(severity).toUpperCase();
    if (upper === "CRITICAL" || upper === "HIGH") {
      return (
        <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-red-100 text-red-800 rounded border border-red-200">
          {formatImportance(severity)} Severity
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-amber-100 text-amber-800 rounded border border-amber-200">
        {formatImportance(severity)} Severity
      </span>
    );
  };

  return (
    <div className="space-y-8 bg-white p-6 md:p-8 rounded-xl border border-slate-200 shadow-sm">
      {/* Header */}
      <div className="border-b border-slate-100 pb-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-600" />
            Drive Intelligence Profile
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Comprehensive structured intelligence extracted from the job description.
          </p>
        </div>
        {payload.intelligence_schema_version && (
          <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2.5 py-1 rounded border border-slate-200 self-start md:self-auto">
            Schema {payload.intelligence_schema_version}
          </span>
        )}
      </div>

      {/* 1. Executive Difficulty & Alignment Section */}
      {(difficulty || placementRelevance) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-5 bg-gradient-to-br from-indigo-50/60 to-slate-50 rounded-xl border border-indigo-100/80">
          {/* Difficulty Assessment */}
          {difficulty && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Target className="w-4 h-4 text-indigo-600" />
                  Drive Difficulty Assessment
                </h3>
                <span className="px-3 py-1 bg-indigo-600 text-white text-xs font-bold rounded-full shadow-sm">
                  {formatDifficultyLevel(difficulty.level)}
                </span>
              </div>
              {difficulty.reasoning && (
                <p className="text-sm text-slate-700 leading-relaxed font-normal bg-white/80 p-3 rounded-lg border border-indigo-100">
                  {difficulty.reasoning}
                </p>
              )}
              {Array.isArray(difficulty.difficulty_factors) && difficulty.difficulty_factors.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {difficulty.difficulty_factors.map((factor: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-2.5 py-0.5 bg-white text-indigo-900 text-xs font-medium rounded-md border border-indigo-200 shadow-2xs"
                    >
                      {factor}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Placement Relevance Archetypes */}
          {placementRelevance && (
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                Target Candidate Profiles & Alignment
              </h3>
              {Array.isArray(placementRelevance.target_candidate_profiles) && placementRelevance.target_candidate_profiles.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-500 uppercase mb-1.5">Target Archetypes</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {placementRelevance.target_candidate_profiles.map((profile: string, idx: number) => (
                      <span key={idx} className="px-2.5 py-1 bg-white text-slate-800 text-xs font-semibold rounded-md border border-slate-200 shadow-2xs">
                        {profile}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {Array.isArray(placementRelevance.preparation_priorities) && placementRelevance.preparation_priorities.length > 0 && (
                <div className="pt-1">
                  <h4 className="text-xs font-semibold text-slate-500 uppercase mb-1.5">Preparation Priorities</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {placementRelevance.preparation_priorities.map((prio: string, idx: number) => (
                      <span key={idx} className="px-2 py-0.5 bg-indigo-50 text-indigo-700 text-xs font-medium rounded border border-indigo-100">
                        {prio}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 2. Technologies & Qualifications Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Required Technologies */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-indigo-600" />
              Required & Expected Technologies
            </h3>
            <span className="text-xs font-medium text-slate-400">
              {technologies.length} identified
            </span>
          </div>

          {technologies.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {technologies.map((tech: any, i: number) => {
                const isCritical = String(tech.importance).toUpperCase() === "CRITICAL";
                const isMandatory = tech.is_mandatory === true;
                return (
                  <div
                    key={i}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                      isCritical
                        ? "bg-rose-50 text-rose-800 border-rose-200 shadow-2xs"
                        : "bg-indigo-50/80 text-indigo-800 border-indigo-200/80"
                    }`}
                  >
                    <span>{tech.name || "Unknown"}</span>
                    {isCritical && (
                      <span className="px-1.5 py-0.2 bg-rose-200 text-rose-900 rounded text-[9px] font-bold uppercase">
                        Critical
                      </span>
                    )}
                    {isMandatory && !isCritical && (
                      <span className="px-1.5 py-0.2 bg-amber-200 text-amber-900 rounded text-[9px] font-bold uppercase">
                        Must-Have
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400 italic bg-slate-50 p-4 rounded-lg border border-slate-100">
              No specific technology requirements extracted.
            </p>
          )}
        </section>

        {/* Qualifications & Eligibility */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2">
              <GraduationCap className="w-4 h-4 text-emerald-600" />
              Eligibility Criteria & Constraints
            </h3>
            <span className="text-xs font-medium text-slate-400">
              {qualifications.length} criteria
            </span>
          </div>

          {qualifications.length > 0 ? (
            <div className="space-y-2.5">
              {qualifications.map((qual: any, i: number) => {
                const evidenceText = qual.evidence?.[0]?.source_text;
                return (
                  <div key={i} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-slate-800">
                        {qual.qualification_type ? formatCompetency(qual.qualification_type) : "Eligibility Cutoff"}
                      </span>
                      {qual.is_mandatory && (
                        <span className="px-1.5 py-0.5 bg-rose-100 text-rose-800 text-[10px] font-bold uppercase rounded">
                          Mandatory
                        </span>
                      )}
                    </div>
                    {qual.allowed_values && Array.isArray(qual.allowed_values) && (
                      <p className="text-xs text-slate-600 mt-1">
                        Allowed: <span className="font-medium text-slate-900">{qual.allowed_values.join(", ")}</span>
                      </p>
                    )}
                    {qual.numeric_value !== null && qual.numeric_value !== undefined && (
                      <p className="text-xs text-slate-600 mt-1">
                        Constraint: <span className="font-medium text-slate-900">{qual.operator || ">="} {qual.numeric_value}</span>
                      </p>
                    )}
                    {evidenceText && (
                      <div className="mt-1.5 text-xs text-slate-500 italic flex items-start gap-1 bg-white/70 p-1.5 rounded border border-slate-100">
                        <Quote className="w-3 h-3 text-slate-400 shrink-0 mt-0.5" />
                        <span>{evidenceText}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400 italic bg-slate-50 p-4 rounded-lg border border-slate-100">
              No hard qualification constraints specified.
            </p>
          )}
        </section>
      </div>

      {/* 3. Competencies Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6 border-t border-slate-100">
        {/* Technical Competencies */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Technical Hard Competencies
            </h3>
            <span className="text-xs font-medium text-slate-400">
              {techCompetencies.length} competencies
            </span>
          </div>

          {techCompetencies.length > 0 ? (
            <div className="space-y-3">
              {techCompetencies.map((comp: any, i: number) => {
                const label = formatCompetency(comp.competency || comp.name);
                const evidenceText = comp.evidence?.[0]?.source_text;
                return (
                  <div key={i} className="p-3 bg-slate-50/80 rounded-lg border border-slate-200">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                        <span className="w-2 h-2 bg-emerald-500 rounded-full shrink-0" />
                        {label}
                      </span>
                      {renderImportanceBadge(comp.importance)}
                    </div>
                    {evidenceText && (
                      <div className="mt-2 text-xs text-slate-600 italic flex items-start gap-1.5 bg-white p-2 rounded border border-slate-200/80">
                        <Quote className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                        <span>{evidenceText}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400 italic bg-slate-50 p-4 rounded-lg border border-slate-100">
              No technical competencies identified.
            </p>
          )}
        </section>

        {/* Behavioral Competencies */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2">
              <User className="w-4 h-4 text-blue-600" />
              Behavioral & Soft Skills
            </h3>
            <span className="text-xs font-medium text-slate-400">
              {behaviors.length} skills
            </span>
          </div>

          {behaviors.length > 0 ? (
            <div className="space-y-3">
              {behaviors.map((beh: any, i: number) => {
                const label = formatBehavioralSkill(beh.competency || beh.name);
                const evidenceText = beh.evidence?.[0]?.source_text;
                return (
                  <div key={i} className="p-3 bg-slate-50/80 rounded-lg border border-slate-200">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                        <span className="w-2 h-2 bg-blue-500 rounded-full shrink-0" />
                        {label}
                      </span>
                      {renderImportanceBadge(beh.importance)}
                    </div>
                    {evidenceText && (
                      <div className="mt-2 text-xs text-slate-600 italic flex items-start gap-1.5 bg-white p-2 rounded border border-slate-200/80">
                        <Quote className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                        <span>{evidenceText}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400 italic bg-slate-50 p-4 rounded-lg border border-slate-100">
              No behavioral competencies identified.
            </p>
          )}
        </section>
      </div>

      {/* 4. Role Expectations & Actionable Responsibilities */}
      {expectations.length > 0 && (
        <div className="pt-6 border-t border-slate-100">
          <section>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-indigo-600" />
                Actionable Role Responsibilities
              </h3>
              <span className="text-xs font-medium text-slate-400">
                {expectations.length} responsibilities
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {expectations.map((exp: any, i: number) => {
                const expectationText = exp.expectation || exp.description;
                const evidenceText = exp.evidence?.[0]?.source_text;
                return (
                  <div key={i} className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex flex-col justify-between">
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <p className="text-sm font-semibold text-slate-900">
                          {expectationText}
                        </p>
                        {renderImportanceBadge(exp.importance)}
                      </div>
                    </div>
                    {evidenceText && evidenceText !== expectationText && (
                      <div className="mt-2 text-xs text-slate-500 italic flex items-start gap-1 bg-white p-2 rounded border border-slate-100">
                        <Quote className="w-3 h-3 text-slate-400 shrink-0 mt-0.5" />
                        <span>{evidenceText}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      )}

      {/* 5. Hiring Signals & Risk Intelligence */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6 border-t border-slate-100">
        {/* Hiring Signals */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-500" />
              Implicit Hiring Preference Signals
            </h3>
            <span className="text-xs font-medium text-slate-400">
              {signals.length} signals
            </span>
          </div>

          {signals.length > 0 ? (
            <div className="space-y-3">
              {signals.map((sig: any, i: number) => {
                const label = formatHiringSignal(sig.signal || sig.description);
                const evidenceText = sig.evidence?.[0]?.source_text;
                return (
                  <div key={i} className="p-3 bg-amber-50/50 rounded-lg border border-amber-200/60">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-amber-950 flex items-center gap-2">
                        <span className="w-2 h-2 bg-amber-500 rounded-full shrink-0" />
                        {label}
                      </span>
                      {renderImportanceBadge(sig.importance)}
                    </div>
                    {evidenceText && (
                      <div className="mt-2 text-xs text-amber-900/80 italic flex items-start gap-1.5 bg-white/80 p-2 rounded border border-amber-100">
                        <Quote className="w-3.5 h-3.5 text-amber-500/70 shrink-0 mt-0.5" />
                        <span>{evidenceText}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400 italic bg-slate-50 p-4 rounded-lg border border-slate-100">
              No implicit hiring signals inferred from the JD.
            </p>
          )}
        </section>

        {/* Risk Intelligence */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-md font-semibold text-rose-800 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-600" />
              Structural Hiring Risks
            </h3>
            <span className="text-xs font-medium text-slate-400">
              {risks.length} risks flagged
            </span>
          </div>

          {risks.length > 0 ? (
            <div className="space-y-3">
              {risks.map((r: any, i: number) => {
                const label = formatRiskType(r.risk || r.description);
                const evidenceText = r.evidence?.[0]?.source_text;
                return (
                  <div key={i} className="p-3 bg-rose-50/60 rounded-lg border border-rose-200/70">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-rose-950 flex items-center gap-2">
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                        {label}
                      </span>
                      {renderSeverityBadge(r.severity)}
                    </div>
                    {evidenceText && (
                      <div className="mt-2 text-xs text-rose-900/80 italic flex items-start gap-1.5 bg-white/80 p-2 rounded border border-rose-100">
                        <Quote className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                        <span>{evidenceText}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400 italic bg-slate-50 p-4 rounded-lg border border-slate-100">
              No structural placement risks flagged for this drive.
            </p>
          )}
        </section>
      </div>

      {/* 6. Selection Rounds & Preparation Guidance (if available) */}
      {(selectionRounds.length > 0 || (preparation?.priority_topics && preparation.priority_topics.length > 0)) && (
        <div className="pt-6 border-t border-slate-100">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Selection Rounds */}
            {selectionRounds.length > 0 && (
              <section>
                <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2 mb-3">
                  <Layers className="w-4 h-4 text-indigo-600" />
                  Selection Process Rounds
                </h3>
                <div className="space-y-2">
                  {selectionRounds.map((round: any, i: number) => (
                    <div key={i} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
                      <div>
                        <span className="text-xs font-bold text-indigo-600 mr-2">Round {i + 1}</span>
                        <span className="text-sm font-semibold text-slate-800">
                          {round.round_name || formatRoundType(round.round_type)}
                        </span>
                      </div>
                      {renderImportanceBadge(round.importance)}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Preparation Topics */}
            {preparation?.priority_topics && preparation.priority_topics.length > 0 && (
              <section>
                <h3 className="text-md font-semibold text-slate-800 flex items-center gap-2 mb-3">
                  <BookOpen className="w-4 h-4 text-emerald-600" />
                  Recommended Preparation Topics
                </h3>
                <div className="space-y-2.5">
                  {preparation.priority_topics.map((topic: any, i: number) => (
                    <div key={i} className="p-3 bg-emerald-50/50 rounded-lg border border-emerald-100">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-bold text-emerald-950">
                          {topic.topic_name}
                        </span>
                        {renderImportanceBadge(topic.importance)}
                      </div>
                      {topic.recommended_focus && (
                        <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                          {topic.recommended_focus}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
