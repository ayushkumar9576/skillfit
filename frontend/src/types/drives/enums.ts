export enum DriveStatus {
  draft = "draft",
  analyzing = "analyzing",
  analysis_failed = "analysis_failed",
  ready = "ready",
  published = "published",
  archived = "archived",
}

export enum DriveSourceType {
  manual = "manual",
  parsed = "parsed",
}

export enum DriveSourceFormat {
  pdf = "pdf",
  text = "text",
}

export enum DriveAnalysisStatus {
  pending = "pending",
  running = "running",
  completed = "completed",
  failed = "failed",
}

export enum TechnologyCategory {
  programming_language = "PROGRAMMING_LANGUAGE",
  framework = "FRAMEWORK",
  database = "DATABASE",
  cloud_platform = "CLOUD_PLATFORM",
  devops_tool = "DEVOPS_TOOL",
  data_technology = "DATA_TECHNOLOGY",
  testing_technology = "TESTING_TECHNOLOGY",
  other = "OTHER",
}

export enum ProfessionalDomainType {
  software_engineering = "SOFTWARE_ENGINEERING",
  data = "DATA",
  ai_ml = "AI_ML",
  security = "SECURITY",
  product = "PRODUCT",
  research = "RESEARCH",
  consulting = "CONSULTING",
  qa_testing = "QA_TESTING",
  hardware_engineering = "HARDWARE_ENGINEERING",
  other = "OTHER",
}

export enum ImportanceLevel {
  low = "LOW",
  medium = "MEDIUM",
  high = "HIGH",
  critical = "CRITICAL",
}

export enum DriveConfidenceLevel {
  low = "LOW",
  medium = "MEDIUM",
  high = "HIGH",
}

export enum EvidenceType {
  explicit_requirement = "EXPLICIT_REQUIREMENT",
  explicit_responsibility = "EXPLICIT_RESPONSIBILITY",
  explicit_qualification = "EXPLICIT_QUALIFICATION",
  explicit_selection = "EXPLICIT_SELECTION_PROCESS",
  inferred_signal = "INFERRED_SIGNAL",
}

export enum EvidenceSection {
  requirements = "REQUIREMENTS",
  responsibilities = "RESPONSIBILITIES",
  qualifications = "QUALIFICATIONS",
  selection_process = "SELECTION_PROCESS",
  benefits = "BENEFITS",
  other = "OTHER",
}

export enum TechnicalCompetencyType {
  backend_development = "BACKEND_DEVELOPMENT",
  frontend_development = "FRONTEND_DEVELOPMENT",
  system_design = "SYSTEM_DESIGN",
  cloud_engineering = "CLOUD_ENGINEERING",
  data_engineering = "DATA_ENGINEERING",
  problem_solving = "PROBLEM_SOLVING",
  machine_learning = "MACHINE_LEARNING",
  devops = "DEVOPS",
  mobile_development = "MOBILE_DEVELOPMENT",
  security_engineering = "SECURITY_ENGINEERING",
}

export enum BehavioralCompetencyType {
  communication = "COMMUNICATION",
  leadership = "LEADERSHIP",
  teamwork = "TEAMWORK",
  ownership = "OWNERSHIP",
  adaptability = "ADAPTABILITY",
  critical_thinking = "CRITICAL_THINKING",
  time_management = "TIME_MANAGEMENT",
}

export enum QualificationType {
  cgpa = "CGPA",
  degree = "DEGREE",
  branch = "BRANCH",
  graduation_year = "GRADUATION_YEAR",
  backlog_rule = "BACKLOG_RULE",
  work_authorization = "WORK_AUTHORIZATION",
}

export enum SelectionRoundType {
  online_assessment = "ONLINE_ASSESSMENT",
  technical_interview = "TECHNICAL_INTERVIEW",
  managerial_interview = "MANAGERIAL_INTERVIEW",
  hr_interview = "HR_INTERVIEW",
  group_discussion = "GROUP_DISCUSSION",
  case_study = "CASE_STUDY",
}

export enum HiringSignalType {
  dsa_focused = "DSA_FOCUSED",
  project_focused = "PROJECT_FOCUSED",
  research_focused = "RESEARCH_FOCUSED",
  cloud_focused = "CLOUD_FOCUSED",
  product_focused = "PRODUCT_FOCUSED",
  development_focused = "DEVELOPMENT_FOCUSED",
  open_source_focused = "OPEN_SOURCE_FOCUSED",
}

export enum RiskType {
  strict_eligibility = "STRICT_ELIGIBILITY",
  high_competition = "HIGH_COMPETITION",
  niche_technology_requirement = "NICHE_TECHNOLOGY_REQUIREMENT",
  multi_round_process = "MULTI_ROUND_PROCESS",
  bond_or_contract = "BOND_OR_CONTRACT",
  unclear_role_expectations = "UNCLEAR_ROLE_EXPECTATIONS",
  aggressive_selection_process = "AGGRESSIVE_SELECTION_PROCESS",
  high_skill_density = "HIGH_SKILL_DENSITY",
}

export enum SuccessIndicatorType {
  strong_dsa = "STRONG_DSA",
  strong_projects = "STRONG_PROJECTS",
  internship_experience = "INTERNSHIP_EXPERIENCE",
  open_source_contributions = "OPEN_SOURCE_CONTRIBUTIONS",
  leadership_experience = "LEADERSHIP_EXPERIENCE",
  hackathon_experience = "HACKATHON_EXPERIENCE",
  research_experience = "RESEARCH_EXPERIENCE",
}

export enum SuccessIndicatorStrength {
  required = "REQUIRED",
  preferred = "PREFERRED",
  bonus = "BONUS",
}

export enum QualificationOperator {
  gte = "GTE",
  lte = "LTE",
  eq = "EQ",
  in_op = "IN",
  not_in = "NOT_IN",
}

export enum WorkMode {
  remote = "REMOTE",
  hybrid = "HYBRID",
  on_site = "ON_SITE",
}

export enum ShiftType {
  general = "GENERAL",
  rotational = "ROTATIONAL",
  night = "NIGHT_SHIFT",
}

export enum ExperienceLevel {
  fresher = "FRESHER",
  internship = "INTERNSHIP",
  lateral = "LATERAL",
}

export enum IntelligenceOrigin {
  explicit = "EXPLICIT",
  inferred_role = "INFERRED_ROLE",
  inferred_domain = "INFERRED_DOMAIN",
  inferred_responsibility = "INFERRED_RESPONSIBILITY",
}

export enum IndustryVertical {
  fintech = "FINTECH",
  edtech = "EDTECH",
  healthcare = "HEALTHCARE",
  e_commerce = "E_COMMERCE",
  enterprise_saas = "ENTERPRISE_SAAS",
  automotive = "AUTOMOTIVE",
  consulting = "CONSULTING",
  gaming = "GAMING",
  cybersecurity = "CYBERSECURITY",
  other = "OTHER",
}

export enum DriveDifficultyLevel {
  beginner = "BEGINNER",
  moderate = "MODERATE",
  competitive = "COMPETITIVE",
  highly_competitive = "HIGHLY_COMPETITIVE",
  elite = "ELITE",
}
