/* eslint-disable @typescript-eslint/no-explicit-any */
import {
  CandidateIntelligenceProfile,
  TechnologyIntelligence,
  CompetencyIntelligence,
  SkillIntelligence,
  DomainIntelligence,
  WorkplaceExposure,
  EngineeringSignal,
  OwnershipIntelligence,
  Finding,
  Recommendation,
  CertificationIntelligence,
  IntelligenceEvidence,
  DemonstrationLevel,
  VerificationStatus,
  OwnershipLevel,
  FindingType,
  FindingSeverity,
  IntelligenceSourceType,
  EngineeringSignalCategory,
  DomainType,
  ProfileMetadata,
  CandidateSummary
} from "@/types/candidate-profile";

function safeEnum<T extends Record<string, string>>(enumObj: T, value: any, fallback: T[keyof T]): T[keyof T] {
  if (!value) return fallback;
  const upperVal = String(value).toUpperCase();
  if (Object.values(enumObj).includes(upperVal as any)) {
    return upperVal as T[keyof T];
  }
  return fallback;
}

function mapEvidence(evidenceList: any[] = []): IntelligenceEvidence[] {
  if (!Array.isArray(evidenceList)) return [];
  return evidenceList.map((e: any): IntelligenceEvidence => ({
    source: safeEnum(IntelligenceSourceType, e?.source, IntelligenceSourceType.SELF_REPORTED),
    source_id: e?.source_id || "",
    section: e?.section || "",
    quote: e?.quote || "",
    line_reference: e?.line_reference ?? null
  }));
}

export function mapCandidateProfile(raw: any): CandidateIntelligenceProfile {
  if (!raw) {
    throw new Error("Cannot map empty profile");
  }

  const technologies: TechnologyIntelligence[] = Array.isArray(raw.technologies) ? raw.technologies.map((t: any) => ({
    technology: t?.technology || "Unknown",
    demonstration_level: safeEnum(DemonstrationLevel, t?.demonstration_level, DemonstrationLevel.CLAIMED),
    evidence: mapEvidence(t?.evidence),
    source_types: Array.isArray(t?.source_types) ? t.source_types : []
  })) : [];

  const competencies: CompetencyIntelligence[] = Array.isArray(raw.competencies) ? raw.competencies.map((c: any) => ({
    competency: c?.competency || "Unknown",
    demonstrated: Boolean(c?.demonstrated),
    demonstration_level: safeEnum(DemonstrationLevel, c?.demonstration_level, DemonstrationLevel.CLAIMED),
    evidence: mapEvidence(c?.evidence),
    supporting_technologies: Array.isArray(c?.supporting_technologies) ? c.supporting_technologies : [],
    supporting_projects: Array.isArray(c?.supporting_projects) ? c.supporting_projects : []
  })) : [];

  const domains: DomainIntelligence[] = Array.isArray(raw.domains) ? raw.domains.map((d: any) => ({
    domain: safeEnum(DomainType, d?.domain, DomainType.BACKEND), // Using Backend as generic fallback if unknown
    supporting_competencies: Array.isArray(d?.supporting_competencies) ? d.supporting_competencies : [],
    supporting_technologies: Array.isArray(d?.supporting_technologies) ? d.supporting_technologies : [],
    evidence: mapEvidence(d?.evidence)
  })) : [];

  const skills: SkillIntelligence[] = Array.isArray(raw.skills) ? raw.skills.map((s: any) => ({
    skill: s?.skill || "Unknown",
    verification_status: safeEnum(VerificationStatus, s?.verification_status, VerificationStatus.UNVERIFIED),
    demonstration_level: safeEnum(DemonstrationLevel, s?.demonstration_level, DemonstrationLevel.CLAIMED),
    evidence: mapEvidence(s?.evidence),
    evidence_count: typeof s?.evidence_count === 'number' ? s.evidence_count : 0
  })) : [];

  const certifications: CertificationIntelligence[] = Array.isArray(raw.certifications) ? raw.certifications.map((c: any) => ({
    certification_name: c?.certification_name || "Unknown",
    category: c?.category || "Unknown",
    supported_competencies: Array.isArray(c?.supported_competencies) ? c.supported_competencies : [],
    supported_domains: Array.isArray(c?.supported_domains) ? c.supported_domains : [],
    industry_recognition: c?.industry_recognition || "Unknown",
    practical_strength: c?.practical_strength || "Unknown",
    limitations: Array.isArray(c?.limitations) ? c.limitations : [],
    evidence: mapEvidence(c?.evidence)
  })) : [];

  const ownership_signals: OwnershipIntelligence[] = Array.isArray(raw.ownership_signals) ? raw.ownership_signals.map((o: any) => ({
    signal: o?.signal || "Unknown",
    ownership_level: safeEnum(OwnershipLevel, o?.ownership_level, OwnershipLevel.OBSERVED),
    evidence: mapEvidence(o?.evidence)
  })) : [];

  const engineering_signals: EngineeringSignal[] = Array.isArray(raw.engineering_signals) ? raw.engineering_signals.map((e: any) => ({
    category: safeEnum(EngineeringSignalCategory, e?.category, EngineeringSignalCategory.INTEGRATION),
    signal: e?.signal || "Unknown",
    demonstrated: Boolean(e?.demonstrated),
    evidence: mapEvidence(e?.evidence)
  })) : [];

  const workplace_exposure: WorkplaceExposure[] = Array.isArray(raw.workplace_exposure) ? raw.workplace_exposure.map((w: any) => ({
    exposure_type: w?.exposure_type || "Unknown",
    evidence: mapEvidence(w?.evidence)
  })) : [];

  const findings: Finding[] = Array.isArray(raw.findings) ? raw.findings.map((f: any) => ({
    type: safeEnum(FindingType, f?.type, FindingType.MISSING_SIGNAL),
    severity: safeEnum(FindingSeverity, f?.severity, FindingSeverity.LOW),
    title: f?.title || "Finding",
    description: f?.description || "",
    evidence: mapEvidence(f?.evidence)
  })) : [];

  const recommendations: Recommendation[] = Array.isArray(raw.recommendations) ? raw.recommendations.map((r: any) => ({
    title: r?.title || "Recommendation",
    description: r?.description || "",
    derived_from: Array.isArray(r?.derived_from) ? r.derived_from : [],
    estimated_impact: r?.estimated_impact || "Low",
    priority: r?.priority || "Low",
    target_competencies: Array.isArray(r?.target_competencies) ? r.target_competencies : []
  })) : [];

  const metadata: ProfileMetadata = {
    total_projects_analyzed: raw.metadata?.total_projects_analyzed || 0,
    total_internships_analyzed: raw.metadata?.total_internships_analyzed || 0,
    total_certifications_analyzed: raw.metadata?.total_certifications_analyzed || 0,
    analysis_version: raw.metadata?.analysis_version || "unknown"
  };

  const summary: CandidateSummary = {
    primary_domains: Array.isArray(raw.summary?.primary_domains) ? raw.summary.primary_domains : [],
    strongest_competencies: Array.isArray(raw.summary?.strongest_competencies) ? raw.summary.strongest_competencies : [],
    strongest_technologies: Array.isArray(raw.summary?.strongest_technologies) ? raw.summary.strongest_technologies : [],
    largest_gaps: Array.isArray(raw.summary?.largest_gaps) ? raw.summary.largest_gaps : [],
    readiness_highlights: Array.isArray(raw.summary?.readiness_highlights) ? raw.summary.readiness_highlights : []
  };

  return {
    technologies,
    competencies,
    domains,
    skills,
    certifications,
    ownership_signals,
    engineering_signals,
    workplace_exposure,
    findings,
    recommendations,
    summary,
    metadata,
    project_sophistication: raw.project_sophistication || [],
    average_project_sophistication: raw.average_project_sophistication || null,
    highest_project_sophistication: raw.highest_project_sophistication || null
  };
}
