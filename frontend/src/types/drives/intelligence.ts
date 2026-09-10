import {
  EvidenceType,
  DriveConfidenceLevel,
  EvidenceSection,
  TechnologyCategory,
  ImportanceLevel,
  IntelligenceOrigin,
  ProfessionalDomainType,
  IndustryVertical,
  TechnicalCompetencyType,
  BehavioralCompetencyType,
  QualificationType,
  QualificationOperator,
  HiringSignalType,
  SelectionRoundType,
  RiskType,
  SuccessIndicatorType,
  SuccessIndicatorStrength,
  WorkMode,
  ShiftType,
  ExperienceLevel,
  DriveDifficultyLevel,
} from "./enums";

export interface Evidence {
  source_text: string;
  evidence_type: EvidenceType;
  confidence: DriveConfidenceLevel;
  source_section: EvidenceSection;
}

export interface TechnologyIntelligence {
  name: string;
  category: TechnologyCategory;
  importance: ImportanceLevel;
  confidence: DriveConfidenceLevel;
  is_mandatory: boolean | null;
  origin: IntelligenceOrigin;
  evidence: Evidence[];
}

export interface ProfessionalDomainIntelligence {
  domain: ProfessionalDomainType;
  subdomains: string[];
  role_family: string | null;
  industry: IndustryVertical | null;
  confidence: DriveConfidenceLevel;
  evidence: Evidence[];
}

export interface TechnicalCompetencyIntelligence {
  competency: TechnicalCompetencyType;
  importance: ImportanceLevel;
  confidence: DriveConfidenceLevel;
  origin: IntelligenceOrigin;
  evidence: Evidence[];
}

export interface BehavioralCompetencyIntelligence {
  competency: BehavioralCompetencyType;
  importance: ImportanceLevel;
  confidence: DriveConfidenceLevel;
  origin: IntelligenceOrigin;
  evidence: Evidence[];
}

export interface QualificationIntelligence {
  qualification_type: QualificationType;
  operator: QualificationOperator;
  numeric_value: number | null;
  allowed_values: string[] | null;
  is_mandatory: boolean;
  confidence: DriveConfidenceLevel;
  evidence: Evidence[];
}

export interface HiringSignal {
  signal: HiringSignalType;
  importance: ImportanceLevel;
  confidence: DriveConfidenceLevel;
  evidence: Evidence[];
}

export interface RoleExpectation {
  expectation: string;
  importance: ImportanceLevel;
  origin: IntelligenceOrigin;
  evidence: Evidence[];
}

export interface SelectionProcessIntelligence {
  round_name: string;
  round_type: SelectionRoundType;
  importance: ImportanceLevel;
  evidence: Evidence[];
}

export interface RiskIntelligence {
  risk: RiskType;
  severity: ImportanceLevel;
  evidence: Evidence[];
}

export interface SuccessIndicator {
  indicator: SuccessIndicatorType;
  strength: SuccessIndicatorStrength;
  evidence: Evidence[];
}

export interface ServiceAgreementIntelligence {
  has_bond: boolean;
  duration_months: number | null;
  penalty_amount: number | null;
  evidence: Evidence[];
}

export interface WorkArrangementIntelligence {
  mode: WorkMode;
  locations: string[];
  evidence: Evidence[];
}

export interface ShiftIntelligence {
  shift_type: ShiftType;
  evidence: Evidence[];
}

export interface ExperienceIntelligence {
  level: ExperienceLevel;
  min_months: number | null;
  evidence: Evidence[];
}

export interface CompensationIntelligence {
  fixed_compensation: number | null;
  variable_compensation: number | null;
  joining_bonus: number | null;
  esop_value: number | null;
  total_ctc: number | null;
  currency: string;
  evidence: Evidence[];
}

export interface PreparationTopic {
  topic_name: string;
  importance: ImportanceLevel;
  target_round_type: SelectionRoundType;
  recommended_focus: string;
  evidence: Evidence[];
}

export interface PreparationIntelligence {
  priority_topics: PreparationTopic[];
  key_evaluation_focus: string[];
}

export interface DriveDifficultyIntelligence {
  level: DriveDifficultyLevel;
  difficulty_factors: string[];
  reasoning: string;
  confidence: DriveConfidenceLevel;
  evidence: Evidence[];
}

export interface PlacementRelevanceIntelligence {
  target_candidate_profiles: string[];
  preferred_backgrounds: string[];
  project_alignment_areas: string[];
  preparation_priorities: string[];
  confidence: DriveConfidenceLevel;
  evidence: Evidence[];
}

export interface DriveIntelligenceProfile {
  intelligence_schema_version: string;
  domain: ProfessionalDomainIntelligence | null;
  technologies: TechnologyIntelligence[];
  technical_competencies: TechnicalCompetencyIntelligence[];
  behavioral_competencies: BehavioralCompetencyIntelligence[];
  qualifications: QualificationIntelligence[];
  hiring_signals: HiringSignal[];
  role_expectations: RoleExpectation[];
  selection_process: SelectionProcessIntelligence[];
  risks: RiskIntelligence[];
  success_indicators: SuccessIndicator[];
  service_agreements: ServiceAgreementIntelligence[];
  work_arrangements: WorkArrangementIntelligence[];
  shifts: ShiftIntelligence[];
  experience_requirements: ExperienceIntelligence[];
  compensation: CompensationIntelligence[];
  preparation: PreparationIntelligence | null;
  difficulty: DriveDifficultyIntelligence | null;
  placement_relevance: PlacementRelevanceIntelligence | null;
}
