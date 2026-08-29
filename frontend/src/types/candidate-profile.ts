/**
 * Canonical Frontend Intelligence Models
 * --------------------------------------
 * 1:1 representation of backend/app/analysis/models/candidate_profile.py
 * 
 * Do NOT add UI-specific fields to these models.
 * Do NOT introduce frontend aliases.
 */

export enum IntelligenceSourceType {
  PROJECT = "project",
  INTERNSHIP = "internship",
  CERTIFICATION = "certification",
  SELF_REPORTED = "self_reported",
}

export enum DemonstrationLevel {
  CLAIMED = "CLAIMED",
  REFERENCED = "REFERENCED",
  USED = "USED",
  IMPLEMENTED = "IMPLEMENTED",
  DESIGNED = "DESIGNED",
  ARCHITECTED = "ARCHITECTED",
}

export enum OwnershipLevel {
  OBSERVED = "OBSERVED",
  CONTRIBUTED = "CONTRIBUTED",
  IMPLEMENTED = "IMPLEMENTED",
  OWNED = "OWNED",
  LED = "LED",
}

export enum VerificationStatus {
  UNVERIFIED = "UNVERIFIED",
  WEAKLY_VERIFIED = "WEAKLY_VERIFIED",
  VERIFIED = "VERIFIED",
  STRONGLY_VERIFIED = "STRONGLY_VERIFIED",
}

export enum FindingType {
  STRENGTH = "STRENGTH",
  WEAKNESS = "WEAKNESS",
  MISSING_SIGNAL = "MISSING_SIGNAL",
}

export enum FindingSeverity {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum EngineeringSignalCategory {
  ARCHITECTURE = "ARCHITECTURE",
  DEPLOYMENT = "DEPLOYMENT",
  TESTING = "TESTING",
  SECURITY = "SECURITY",
  MONITORING = "MONITORING",
  INTEGRATION = "INTEGRATION",
}

export enum DomainType {
  MACHINE_LEARNING = "MACHINE_LEARNING",
  BACKEND = "BACKEND",
  FRONTEND = "FRONTEND",
  CLOUD = "CLOUD",
  DEVOPS = "DEVOPS",
  DATA_ENGINEERING = "DATA_ENGINEERING",
  SECURITY = "SECURITY",
  MOBILE = "MOBILE",
  FULL_STACK = "FULL_STACK",
  DATA_SCIENCE = "DATA_SCIENCE",
  MLOPS = "MLOPS",
  DISTRIBUTED_SYSTEMS = "DISTRIBUTED_SYSTEMS",
}

export interface IntelligenceEvidence {
  source: IntelligenceSourceType;
  source_id: string;
  section: string;
  quote: string;
  line_reference: number | null;
}

export interface TechnologyIntelligence {
  technology: string;
  demonstration_level: string; // Should map to DemonstrationLevel
  evidence: IntelligenceEvidence[];
  source_types: string[]; // Should map to IntelligenceSourceType[]
}

export interface CompetencyIntelligence {
  competency: string;
  demonstrated: boolean;
  demonstration_level: string;
  evidence: IntelligenceEvidence[];
  supporting_technologies: string[];
  supporting_projects: string[];
}

export interface SkillIntelligence {
  skill: string;
  verification_status: string; // Should map to VerificationStatus
  demonstration_level: string;
  evidence: IntelligenceEvidence[];
  evidence_count: number;
}

export interface DomainIntelligence {
  domain: string;
  supporting_competencies: string[];
  supporting_technologies: string[];
  evidence: IntelligenceEvidence[];
}

export interface WorkplaceExposure {
  exposure_type: string;
  evidence: IntelligenceEvidence[];
}

export interface EngineeringSignal {
  category: string;
  signal: string;
  demonstrated: boolean;
  evidence: IntelligenceEvidence[];
}

export interface OwnershipIntelligence {
  signal: string;
  ownership_level: string;
  evidence: IntelligenceEvidence[];
}

export interface Finding {
  type: string; // Maps to FindingType
  severity: string; // Maps to FindingSeverity
  title: string;
  description: string;
  evidence: IntelligenceEvidence[];
}

export interface Recommendation {
  title: string;
  description: string;
  derived_from: string[];
  estimated_impact: string;
  priority: string;
  target_competencies: string[];
}

export interface CertificationIntelligence {
  certification_name: string;
  category: string;
  supported_competencies: string[];
  supported_domains: string[];
  industry_recognition: string;
  practical_strength: string;
  limitations: string[];
  evidence: IntelligenceEvidence[];
}

export interface ProfileMetadata {
  total_projects_analyzed: number;
  total_internships_analyzed: number;
  total_certifications_analyzed: number;
  analysis_version: string;
}

export interface CandidateSummary {
  primary_domains: string[];
  strongest_competencies: string[];
  strongest_technologies: string[];
  largest_gaps: string[];
  readiness_highlights: string[];
}

export interface CandidateIntelligenceProfile {
  technologies: TechnologyIntelligence[];
  competencies: CompetencyIntelligence[];
  domains: DomainIntelligence[];
  skills: SkillIntelligence[];
  certifications: CertificationIntelligence[];
  ownership_signals: OwnershipIntelligence[];
  engineering_signals: EngineeringSignal[];
  workplace_exposure: WorkplaceExposure[];
  findings: Finding[];
  recommendations: Recommendation[];
  summary: CandidateSummary;
  metadata: ProfileMetadata;
}
