/**
 * frontend/src/lib/mappers/drive-intelligence.ts
 * -----------------------------------------------
 * Human-readable label mappers for Drive Intelligence enums.
 * Converts raw backend enum values into clear, user-friendly labels,
 * with graceful fallback to Title Case for unknown or novel enum members.
 */

export function formatTitleCase(str?: string | null): string {
  if (!str) return "";
  return str
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

const TECHNICAL_COMPETENCY_LABELS: Record<string, string> = {
  BACKEND_DEVELOPMENT: "Backend Development",
  FRONTEND_DEVELOPMENT: "Frontend Development",
  FULL_STACK_DEVELOPMENT: "Full-Stack Development",
  SYSTEM_DESIGN: "System Design",
  DATA_ENGINEERING: "Data Engineering",
  PROBLEM_SOLVING: "Problem Solving & DSA",
  MACHINE_LEARNING: "Machine Learning",
  DEEP_LEARNING: "Deep Learning",
  DATA_SCIENCE: "Data Science",
  CLOUD_COMPUTING: "Cloud Computing",
  CLOUD_ENGINEERING: "Cloud Engineering",
  DEVOPS: "DevOps & CI/CD",
  MLOPS: "MLOps",
  MOBILE_DEVELOPMENT: "Mobile Development",
  SECURITY_ENGINEERING: "Security Engineering",
  CYBERSECURITY: "Cybersecurity",
  SOFTWARE_ARCHITECTURE: "Software Architecture",
  DATABASE_DESIGN: "Database Design",
  API_DEVELOPMENT: "API Development",
  TESTING: "Software Testing",
  QA_AUTOMATION: "QA Automation",
  DISTRIBUTED_SYSTEMS: "Distributed Systems",
};

export function formatCompetency(val?: string | null): string {
  if (!val) return "Unspecified Competency";
  const upper = String(val).trim().toUpperCase();
  return TECHNICAL_COMPETENCY_LABELS[upper] || formatTitleCase(val);
}

const BEHAVIORAL_COMPETENCY_LABELS: Record<string, string> = {
  COMMUNICATION: "Communication",
  LEADERSHIP: "Leadership",
  TEAMWORK: "Teamwork & Collaboration",
  OWNERSHIP: "Ownership & Accountability",
  ADAPTABILITY: "Adaptability & Agility",
  CRITICAL_THINKING: "Critical Thinking",
  TIME_MANAGEMENT: "Time Management",
};

export function formatBehavioralSkill(val?: string | null): string {
  if (!val) return "Unspecified Skill";
  const upper = String(val).trim().toUpperCase();
  return BEHAVIORAL_COMPETENCY_LABELS[upper] || formatTitleCase(val);
}

const HIRING_SIGNAL_LABELS: Record<string, string> = {
  DSA_FOCUSED: "DSA-Focused Hiring",
  PROJECT_FOCUSED: "Project-Focused Evaluation",
  DEVELOPMENT_FOCUSED: "Development & Engineering Focus",
  RESEARCH_FOCUSED: "Research & Academic Orientation",
  CLOUD_FOCUSED: "Cloud & Infrastructure Focus",
  PRODUCT_FOCUSED: "Product & User-Centric Mindset",
  OPEN_SOURCE_FOCUSED: "Open Source Contribution Focus",
};

export function formatHiringSignal(val?: string | null): string {
  if (!val) return "Unspecified Signal";
  const upper = String(val).trim().toUpperCase();
  return HIRING_SIGNAL_LABELS[upper] || formatTitleCase(val);
}

const RISK_TYPE_LABELS: Record<string, string> = {
  STRICT_ELIGIBILITY: "Strict Eligibility Criteria",
  HIGH_COMPETITION: "High Applicant Competition",
  NICHE_TECHNOLOGY_REQUIREMENT: "Niche Technology Requirements",
  MULTI_ROUND_PROCESS: "Multi-Round Selection Process",
  BOND_OR_CONTRACT: "Service Agreement or Bond Required",
  UNCLEAR_ROLE_EXPECTATIONS: "Unclear Role Expectations",
  AGGRESSIVE_SELECTION_PROCESS: "Aggressive Selection Process",
  HIGH_SKILL_DENSITY: "High Skill Density Required",
};

export function formatRiskType(val?: string | null): string {
  if (!val) return "Unspecified Risk";
  const upper = String(val).trim().toUpperCase();
  return RISK_TYPE_LABELS[upper] || formatTitleCase(val);
}

const DIFFICULTY_LEVEL_LABELS: Record<string, string> = {
  BEGINNER: "Beginner",
  MODERATE: "Moderate",
  COMPETITIVE: "Competitive",
  HIGHLY_COMPETITIVE: "Highly Competitive",
  ELITE: "Elite (Tier-1)",
};

export function formatDifficultyLevel(val?: string | null): string {
  if (!val) return "Moderate";
  const upper = String(val).trim().toUpperCase();
  return DIFFICULTY_LEVEL_LABELS[upper] || formatTitleCase(val);
}

const IMPORTANCE_LABELS: Record<string, string> = {
  CRITICAL: "Critical",
  HIGH: "High",
  MEDIUM: "Medium",
  LOW: "Low",
};

export function formatImportance(val?: string | null): string {
  if (!val) return "Medium";
  const upper = String(val).trim().toUpperCase();
  return IMPORTANCE_LABELS[upper] || formatTitleCase(val);
}

const ROUND_TYPE_LABELS: Record<string, string> = {
  ONLINE_ASSESSMENT: "Online Assessment",
  TECHNICAL_INTERVIEW: "Technical Interview",
  MANAGERIAL_INTERVIEW: "Managerial Interview",
  HR_INTERVIEW: "HR Interview",
  GROUP_DISCUSSION: "Group Discussion",
  CASE_STUDY: "Case Study",
};

export function formatRoundType(val?: string | null): string {
  if (!val) return "Interview Round";
  const upper = String(val).trim().toUpperCase();
  return ROUND_TYPE_LABELS[upper] || formatTitleCase(val);
}
