"""
app/core/enums.py
-----------------
Shared application-level enums.

All modules (models, schemas, services, dependencies, routes) must import
enums from here — never redefine them elsewhere. This prevents circular
imports because this file has zero internal application imports; it only
uses the Python standard library.

Phase history:
    Phase 2-3 — UserRole, AnalysisStatus, ResumeType, ProcessingStatus, etc.
    Phase 4.1 — DriveStatus, DriveSourceType
    Phase 4.2 — DriveSourceFormat, DriveSourceProcessingStatus, DriveSourceValidationStatus
"""

import enum


class UserRole(str, enum.Enum):
    """Roles available in the SkillFit platform."""
    student = "student"
    faculty = "faculty"
    admin = "admin"

class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class ConfidenceLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class ReadinessLevel(str, enum.Enum):
    placement_ready = "placement_ready"
    moderately_ready = "moderately_ready"
    needs_improvement = "needs_improvement"

class ComplexityLabel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"

class TechnicalDepthLabel(str, enum.Enum):
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"

class ExperienceStrengthLabel(str, enum.Enum):
    weak = "weak"
    moderate = "moderate"
    strong = "strong"

class RecordSource(str, enum.Enum):
    resume = "resume"
    manual = "manual"
    imported = "imported"

class ResumeType(str, enum.Enum):
    """
    Supported resume categories on the SkillFit platform.

    Each student may hold exactly one resume per type simultaneously:
        generic      — A general-purpose resume covering all skills and experience.
        specialized  — A role-specific or domain-targeted resume.

    Business rule: max 2 active resumes per student (1 generic + 1 specialized).
    Uploading a new resume of an existing type automatically replaces the old one.
    """
    generic     = "generic"
    specialized = "specialized"

class ProcessingStatus(str, enum.Enum):
    """
    Lifecycle status of the automated resume processing pipeline.

    Transitions:
        uploaded   → File stored, pipeline not yet started.
        processing → Background pipeline is actively running.
        completed  → All pipeline stages finished successfully.
        failed     → One or more pipeline stages encountered an error.
    """
    uploaded   = "uploaded"
    processing = "processing"
    completed  = "completed"
    failed     = "failed"


class DriveStatus(str, enum.Enum):
    """
    Lifecycle status of a Placement Drive entity.

    Transitions (Enforced in Phase 4.4):
        draft           → Drive created (with JD).
        analyzing       → JD is being processed by Intelligence Engine.
        analysis_failed → Intelligence pipeline encountered an error.
        ready           → Intelligence generated successfully. Awaiting Admin review.
        published       → Admin has explicitly published the drive. Visible to students.
        archived        → Drive has concluded; no further activity expected.
    """
    draft = "draft"
    analyzing = "analyzing"
    analysis_failed = "analysis_failed"
    ready = "ready"
    published = "published"
    archived = "archived"


class DriveSourceType(str, enum.Enum):
    """
    Describes how the Placement Drive record was created.

    Phase 4.1 — manual only. Parsed (from JD PDF/text) will be added in
    Phase 4.2 when the Drive Ingestion pipeline is implemented.

    Values:
        manual → Drive data was entered by an admin through the API.
        parsed → Drive data was extracted from a raw job description (Phase 4.2+).
    """
    manual = "manual"
    parsed = "parsed"


class DriveSourceFormat(str, enum.Enum):
    """
    Format of the raw job description source.

    Phase 4.2 — Ingestion pipeline format tracking.

    Values:
        pdf  → Source was uploaded as a PDF file.
        text → Source was submitted as raw text (manual entry).
    """
    pdf  = "pdf"
    text = "text"


class DriveSourceProcessingStatus(str, enum.Enum):
    """
    Lifecycle status of a DriveSource through the ingestion pipeline.

    Phase 4.2 — Ingestion pipeline tracking.

    Transitions:
        uploaded   → File/text received and stored; ingestion not yet started.
        processing → Extraction and normalization are actively running.
        completed  → All pipeline stages finished successfully.
        failed     → One or more pipeline stages encountered an error.
    """
    uploaded   = "uploaded"
    processing = "processing"
    completed  = "completed"
    failed     = "failed"


class DriveSourceValidationStatus(str, enum.Enum):
    """
    Validation status of the ingested source content.

    Phase 4.2 — Source content validation tracking.

    Values:
        pending → Validation has not yet been performed.
        valid   → Source passed all validation checks.
        invalid → Source failed one or more validation checks.
    """
    pending = "pending"
    valid   = "valid"
    invalid = "invalid"


# ===========================================================================
# Phase 4.3 — Drive Intelligence Engine Enums
# ===========================================================================


class DriveAnalysisStatus(str, enum.Enum):
    """
    Lifecycle status of a DriveAnalysis execution run.

    Transitions:
        pending   → Analysis record created; engine not yet started.
        running   → Intelligence Engine is actively processing.
        completed → Engine ran successfully; DriveSnapshot was created.
        failed    → Engine or Governance Layer raised an unrecoverable error.
    """
    pending   = "pending"
    running   = "running"
    completed = "completed"
    failed    = "failed"


class TechnologyCategory(str, enum.Enum):
    """
    Canonical taxonomy for technology classification in Drive Intelligence.

    Governs TechnologyIntelligence.category.  No LLM output may use a value
    outside this set; the Governance Layer treats unknown values as fatal.
    """
    programming_language = "PROGRAMMING_LANGUAGE"
    framework            = "FRAMEWORK"
    database             = "DATABASE"
    cloud_platform       = "CLOUD_PLATFORM"
    devops_tool          = "DEVOPS_TOOL"
    data_technology      = "DATA_TECHNOLOGY"
    testing_technology   = "TESTING_TECHNOLOGY"
    other                = "OTHER"


class ProfessionalDomainType(str, enum.Enum):
    """
    Taxonomy for overarching role business domains.

    Separates the role identity (e.g. Data Scientist) from its hard skills (e.g. Python, SQL).
    """
    software_engineering = "SOFTWARE_ENGINEERING"
    data                 = "DATA"
    ai_ml                = "AI_ML"
    security             = "SECURITY"
    product              = "PRODUCT"
    research             = "RESEARCH"
    consulting           = "CONSULTING"
    qa_testing           = "QA_TESTING"
    hardware_engineering = "HARDWARE_ENGINEERING"
    other                = "OTHER"


class ImportanceLevel(str, enum.Enum):
    """
    Standardized importance model used across all Drive Intelligence artifacts.

    Governs: TechnologyIntelligence, TechnicalCompetencyIntelligence,
    BehavioralCompetencyIntelligence, QualificationIntelligence,
    RoleExpectation, HiringSignal, SuccessIndicator.

    Future use: Phase 5 matching will apply weighted multipliers derived from
    importance. CRITICAL gaps heavily penalize candidate rank; LOW gaps are
    noise-suppressed.
    """
    low      = "LOW"
    medium   = "MEDIUM"
    high     = "HIGH"
    critical = "CRITICAL"


class DriveConfidenceLevel(str, enum.Enum):
    """
    Drive Intelligence confidence model.

    Assignment rules:
        HIGH   → Artifact traces to an explicit, unambiguous statement in the JD.
        MEDIUM → Strongly implied by context; domain knowledge confirms it.
        LOW    → Weakly inferred; uncertain without additional signals.

    Future use: Phase 5 retrieval will suppress LOW confidence signals for
    precision-mode matching and surface them only in exploratory search.
    """
    low    = "LOW"
    medium = "MEDIUM"
    high   = "HIGH"


class EvidenceType(str, enum.Enum):
    """
    Classifies how an evidence snippet was extracted.

    EXPLICIT_* → The JD directly stated the requirement/responsibility/etc.
    INFERRED_SIGNAL → The engine deduced this from surrounding context.
    """
    explicit_requirement    = "EXPLICIT_REQUIREMENT"
    explicit_responsibility = "EXPLICIT_RESPONSIBILITY"
    explicit_qualification  = "EXPLICIT_QUALIFICATION"
    explicit_selection      = "EXPLICIT_SELECTION_PROCESS"
    inferred_signal         = "INFERRED_SIGNAL"


class EvidenceSection(str, enum.Enum):
    """
    Which section of the job description the evidence snippet was found in.

    Enables section-level explainability. The UI can say:
    "Python was found under the REQUIREMENTS section."

    Future: Section-weighted scoring (REQUIREMENTS evidence carries more
    weight than BENEFITS evidence for matching).
    """
    requirements     = "REQUIREMENTS"
    responsibilities = "RESPONSIBILITIES"
    qualifications   = "QUALIFICATIONS"
    selection_process = "SELECTION_PROCESS"
    benefits         = "BENEFITS"
    other            = "OTHER"


class TechnicalCompetencyType(str, enum.Enum):
    """
    Taxonomy for technical/hard-skill competencies expected by the drive.

    Separated from behavioral competencies to enable differentiated Phase 5
    matching. A candidate failing a SYSTEM_DESIGN screen is penalized
    differently than lacking COMMUNICATION signals.
    """
    backend_development  = "BACKEND_DEVELOPMENT"
    frontend_development = "FRONTEND_DEVELOPMENT"
    system_design        = "SYSTEM_DESIGN"
    cloud_engineering    = "CLOUD_ENGINEERING"
    data_engineering     = "DATA_ENGINEERING"
    problem_solving      = "PROBLEM_SOLVING"
    machine_learning     = "MACHINE_LEARNING"
    devops               = "DEVOPS"
    mobile_development   = "MOBILE_DEVELOPMENT"
    security_engineering = "SECURITY_ENGINEERING"


class BehavioralCompetencyType(str, enum.Enum):
    """
    Taxonomy for behavioral/soft-skill competencies expected by the drive.

    Separated from technical competencies.  Phase 5 may apply separate
    behavioral scoring models (e.g., for managerial roles).
    """
    communication = "COMMUNICATION"
    leadership    = "LEADERSHIP"
    teamwork      = "TEAMWORK"
    ownership     = "OWNERSHIP"
    adaptability  = "ADAPTABILITY"
    critical_thinking = "CRITICAL_THINKING"
    time_management   = "TIME_MANAGEMENT"


class QualificationType(str, enum.Enum):
    """
    Taxonomy for eligibility qualification constraints.

    Used by QualificationIntelligence to standardize how eligibility is
    captured, enabling direct comparisons in Phase 5 candidate screening.
    """
    cgpa            = "CGPA"
    degree          = "DEGREE"
    branch          = "BRANCH"
    graduation_year = "GRADUATION_YEAR"
    backlog_rule    = "BACKLOG_RULE"
    work_authorization = "WORK_AUTHORIZATION"


class SelectionRoundType(str, enum.Enum):
    """
    Formal taxonomy for selection process rounds.

    SelectionProcessIntelligence uses this to map out the hiring funnel,
    enabling Phase 5 readiness modules to match candidates against specific
    round types they may struggle with.
    """
    online_assessment   = "ONLINE_ASSESSMENT"
    technical_interview = "TECHNICAL_INTERVIEW"
    managerial_interview = "MANAGERIAL_INTERVIEW"
    hr_interview        = "HR_INTERVIEW"
    group_discussion    = "GROUP_DISCUSSION"
    case_study          = "CASE_STUDY"


class HiringSignalType(str, enum.Enum):
    """
    Taxonomy for implicit hiring preference signals inferred from the JD.

    These are never explicitly stated — they are inferred from emphasis,
    vocabulary, and context (e.g., a JD mentioning LeetCode scores is
    DSA_FOCUSED even if it doesn't say "we value DSA").
    """
    dsa_focused         = "DSA_FOCUSED"
    project_focused     = "PROJECT_FOCUSED"
    research_focused    = "RESEARCH_FOCUSED"
    cloud_focused       = "CLOUD_FOCUSED"
    product_focused     = "PRODUCT_FOCUSED"
    development_focused = "DEVELOPMENT_FOCUSED"
    open_source_focused = "OPEN_SOURCE_FOCUSED"


class RiskType(str, enum.Enum):
    """
    Taxonomy for drive-level risk signals.

    Helps placement officers identify drives with structural challenges,
    and enables Phase 5 to surface risk-aware recommendations.

    Categories:
        strict_eligibility          → Hard cutoffs that filter most students.
        high_competition            → Drive historically attracts many applicants.
        niche_technology_requirement → Requires uncommon or specialized tech.
        multi_round_process         → Many selection stages → high dropout risk.
        bond_or_contract            → Service bond or non-compete clause present.
        unclear_role_expectations   → Vague responsibilities make prep difficult.
        aggressive_selection_process → Fast eliminations, low transparency.
        high_skill_density          → Requires mastery across many domains simultaneously.
    """
    strict_eligibility           = "STRICT_ELIGIBILITY"
    high_competition             = "HIGH_COMPETITION"
    niche_technology_requirement = "NICHE_TECHNOLOGY_REQUIREMENT"
    multi_round_process          = "MULTI_ROUND_PROCESS"
    bond_or_contract             = "BOND_OR_CONTRACT"
    unclear_role_expectations    = "UNCLEAR_ROLE_EXPECTATIONS"
    aggressive_selection_process = "AGGRESSIVE_SELECTION_PROCESS"
    high_skill_density           = "HIGH_SKILL_DENSITY"


class SuccessIndicatorType(str, enum.Enum):
    """
    Taxonomy for candidate traits that signal likely success in the drive.

    These are inferred from what the drive rewards, not what it requires.
    Phase 5 uses these to rank candidates who satisfy eligibility by
    additional competitive differentiation.
    """
    strong_dsa              = "STRONG_DSA"
    strong_projects         = "STRONG_PROJECTS"
    internship_experience   = "INTERNSHIP_EXPERIENCE"
    open_source_contributions = "OPEN_SOURCE_CONTRIBUTIONS"
    leadership_experience   = "LEADERSHIP_EXPERIENCE"
    hackathon_experience    = "HACKATHON_EXPERIENCE"
    research_experience     = "RESEARCH_EXPERIENCE"


class SuccessIndicatorStrength(str, enum.Enum):
    """
    Classifies how strongly a success indicator influences candidate ranking.

    Distinct from ImportanceLevel (which measures eligibility criticality).
    Strength measures *competitive edge*:
        required  → Candidates without this will likely fail selection.
        preferred → Candidates with this have a significant advantage.
        bonus     → Candidates with this receive a minor ranking boost.

    Phase 5: Matching system applies multipliers based on strength to
    separate equally eligible candidates in the ranking layer.
    """
    required  = "REQUIRED"
    preferred = "PREFERRED"
    bonus     = "BONUS"


# ===========================================================================
# Phase 4.3B — Remediation Sprint Constraint Enums
# ===========================================================================


class QualificationOperator(str, enum.Enum):
    """
    Operators for deterministic eligibility execution.
    """
    gte    = "GTE"
    lte    = "LTE"
    eq     = "EQ"
    in_op  = "IN"
    not_in = "NOT_IN"


class WorkMode(str, enum.Enum):
    """
    Taxonomy for work arrangements.
    """
    remote  = "REMOTE"
    hybrid  = "HYBRID"
    on_site = "ON_SITE"


class ShiftType(str, enum.Enum):
    """
    Taxonomy for shift requirements.
    """
    general    = "GENERAL"
    rotational = "ROTATIONAL"
    night      = "NIGHT_SHIFT"


class ExperienceLevel(str, enum.Enum):
    """
    Taxonomy for expected experience levels.
    """
    fresher    = "FRESHER"
    internship = "INTERNSHIP"
    lateral    = "LATERAL"


# ===========================================================================
# Phase 4.5 — Intelligence Enhancement Enums
# ===========================================================================


class IntelligenceOrigin(str, enum.Enum):
    """
    Classifies the provenance of an extracted intelligence artifact.

    Distinguishes whether a skill or expectation was explicitly stated in the JD
    or inferred by the LLM from role title, domain, or stated responsibilities.
    """
    explicit                = "EXPLICIT"
    inferred_role           = "INFERRED_ROLE"
    inferred_domain         = "INFERRED_DOMAIN"
    inferred_responsibility = "INFERRED_RESPONSIBILITY"


class IndustryVertical(str, enum.Enum):
    """
    Taxonomy for industry verticals in Placement Drive Intelligence.

    Captures the primary sector or product category of the hiring organization.
    """
    fintech         = "FINTECH"
    edtech          = "EDTECH"
    healthcare      = "HEALTHCARE"
    e_commerce      = "E_COMMERCE"
    enterprise_saas = "ENTERPRISE_SAAS"
    automotive      = "AUTOMOTIVE"
    consulting      = "CONSULTING"
    gaming          = "GAMING"
    cybersecurity   = "CYBERSECURITY"
    other           = "OTHER"


# ===========================================================================
# Phase 4.4 — Drive Evaluation Engine Enums
# ===========================================================================


class DriveDifficultyLevel(str, enum.Enum):
    """
    Overall competitive difficulty of a Placement Drive.

    Determined by the Drive Evaluation Engine based on a holistic reading of
    the drive's technologies, competencies, selection process, risks, and
    success indicators. Never based on a numeric score.

    Levels:
        BEGINNER          → Entry-level drive; minimal filtering; broad eligibility.
        MODERATE          → Standard hiring process; moderate requirements.
        COMPETITIVE       → Above-average requirements; selective process.
        HIGHLY_COMPETITIVE → Strong signals of high selectivity (e.g. DSA focus,
                             multiple elimination rounds, advanced technology stack).
        ELITE             → Tier-1 company signals combined with extreme selectivity
                            (e.g. Google/Microsoft-scale: Advanced DSA + 5+ rounds).
    """
    beginner           = "BEGINNER"
    moderate           = "MODERATE"
    competitive        = "COMPETITIVE"
    highly_competitive = "HIGHLY_COMPETITIVE"
    elite              = "ELITE"
