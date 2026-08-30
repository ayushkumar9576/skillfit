"""
app/analysis/models/project_models.py
-------------------------------------
Project analysis domain models for SkillFit.

Two layers live here:

    1. Extraction layer (Phase 3.5) — ``ProjectEvidence`` and the
       ``ProjectAnalysisResult`` container. These describe *what was found* in
       the resume text (title, tech, highlights, URL) with light extraction
       confidence.

    2. Intelligence layer (Phase 3.7) — ``ProjectIntelligenceReport`` and its
       supporting structures. These describe *the deep, evidence-based
       technical assessment* of a single project: multi-dimensional complexity,
       engineering depth, per-technology usage, demonstrated competencies,
       skill-evidence mapping, technical maturity, a hiring-signal measure,
       strengths / weaknesses / risks, and an executive assessment.

Design Rules (Phase 3.5 purity, preserved here):
    - Pure standard library dataclasses only.
    - Zero framework dependencies (no SQLAlchemy, FastAPI, Pydantic, or OpenAI).
    - Fully serializable via ``dataclasses.asdict()``.
    - Classification / confidence tiers are stored as plain strings (mirrors the
      ``readiness_level`` / ``proficiency_level`` convention), NOT enums, so this
      layer stays decoupled from every other module.

Evidence-based contract (Phase 3.7 requirement):
    - Every scored dimension carries ``score`` + ``confidence`` + ``reasoning``
      + supporting ``evidence``.
    - Anything that cannot be substantiated from the resume text is set to the
      literal :data:`CANNOT_VERIFY` sentinel — never left silently empty and
      never assumed.

Consumed by:
    - Phase 3.7: Project Analysis Engine (produces ``ProjectIntelligenceReport``)
    - Phase 3.10: Evidence-Based Skill Engine
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from app.analysis.models.base import AnalysisEvidence

class FindingType(str, Enum):
    VERIFIED_FACT = "VERIFIED_FACT"
    ANALYTICAL_OBSERVATION = "ANALYTICAL_OBSERVATION"
    RISK_SIGNAL = "RISK_SIGNAL"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"

class DemonstrationLevel(str, Enum):
    CLAIMED = "CLAIMED"
    MENTIONED = "MENTIONED"
    USED = "USED"
    IMPLEMENTED = "IMPLEMENTED"
    ARCHITECTED = "ARCHITECTED"

# ---------------------------------------------------------------------------
# Evidence-based vocabulary (plain-string tiers — no enum coupling)
# ---------------------------------------------------------------------------

#: Canonical sentinel emitted whenever an assessment cannot be substantiated.
CANNOT_VERIFY: str = "Cannot be verified from available evidence."

# Confidence / verification tiers for a finding.
VERIFICATION_VERIFIED: str = "verified"
VERIFICATION_LIKELY: str = "likely"
VERIFICATION_UNCERTAIN: str = "uncertain"
VERIFICATION_CANNOT_VERIFY: str = "cannot_verify"
VERIFICATION_LEVELS: tuple[str, ...] = (
    VERIFICATION_VERIFIED,
    VERIFICATION_LIKELY,
    VERIFICATION_UNCERTAIN,
    VERIFICATION_CANNOT_VERIFY,
)

# Technical maturity tiers (increasing rigor).
MATURITY_PROTOTYPE: str = "prototype"
MATURITY_ACADEMIC: str = "academic"
MATURITY_PORTFOLIO: str = "portfolio"
MATURITY_PRODUCTION_LIKE: str = "production_like"
MATURITY_INDUSTRY_LEVEL: str = "industry_level"
MATURITY_TIERS: tuple[str, ...] = (
    MATURITY_PROTOTYPE,
    MATURITY_ACADEMIC,
    MATURITY_PORTFOLIO,
    MATURITY_PRODUCTION_LIKE,
    MATURITY_INDUSTRY_LEVEL,
)

# Skill-evidence mapping statuses.
SKILL_CLAIMED: str = "claimed"
SKILL_DEMONSTRATED: str = "demonstrated"
SKILL_VERIFIED: str = "verified"
SKILL_UNVERIFIED: str = "unverified"


# ---------------------------------------------------------------------------
# Sophistication tier vocabulary (computed by Python — never by the LLM)
# ---------------------------------------------------------------------------

class SophisticationTier(str, Enum):
    """
    Deterministic tier classification derived from a project sophistication
    score (0–100). The LLM provides the score; Python derives the tier.

    This mapping is authoritative: all downstream systems and the frontend
    must use this enum as the source of truth.

    Ordering (least → most sophisticated):
        BEGINNER → BASIC → INTERMEDIATE → ADVANCED
        → NEAR_INDUSTRY_READY → INDUSTRY_GRADE
    """
    BEGINNER = "BEGINNER"               # 0–20
    BASIC = "BASIC"                     # 21–40
    INTERMEDIATE = "INTERMEDIATE"       # 41–60
    ADVANCED = "ADVANCED"               # 61–80
    NEAR_INDUSTRY_READY = "NEAR_INDUSTRY_READY"  # 81–90
    INDUSTRY_GRADE = "INDUSTRY_GRADE"   # 91–100


def score_to_tier(score: int) -> str:
    """
    Deterministically derive a SophisticationTier from a 0–100 score.

    Args:
        score: Integer in [0, 100]. Values outside this range are clamped.

    Returns:
        The canonical SophisticationTier string value.

    Example:
        >>> score_to_tier(86)
        'NEAR_INDUSTRY_READY'
        >>> score_to_tier(35)
        'BASIC'
    """
    clamped = max(0, min(100, score))
    if clamped <= 20:
        return SophisticationTier.BEGINNER.value
    if clamped <= 40:
        return SophisticationTier.BASIC.value
    if clamped <= 60:
        return SophisticationTier.INTERMEDIATE.value
    if clamped <= 80:
        return SophisticationTier.ADVANCED.value
    if clamped <= 90:
        return SophisticationTier.NEAR_INDUSTRY_READY.value
    return SophisticationTier.INDUSTRY_GRADE.value


# ---------------------------------------------------------------------------
# Extraction layer (Phase 3.5)
# ---------------------------------------------------------------------------


@dataclass
class ProjectEvidence:
    """
    Represents an extracted project artifact from resume text.

    Attributes:
        title: Project name or title.
        description: Comprehensive summary of the project.
        role: Candidate's role in the project (e.g. 'Sole Developer', 'Backend Lead').
        technologies: List of technologies, languages, and tools utilized.
        project_url: Repository or live deployment URL if available.
        highlights: Key quantifiable bullet points or achievements from the project.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting textual statements.
    """
    title: str
    description: str = ""
    role: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    project_url: Optional[str] = None
    highlights: List[str] = field(default_factory=list)
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Intelligence layer (Phase 3.7) — supporting structures
# ---------------------------------------------------------------------------


@dataclass
class ScoredDimension:
    """
    A single evidence-backed scored dimension.

    This is the reusable unit behind every numeric judgement in the report
    (complexity facets, engineering depth, industry relevance, evidence
    strength, hiring signal). It intentionally bundles the four things the
    evidence-based contract requires of *every* score.

    Attributes:
        name: Machine name of the dimension (e.g. 'overall', 'engineering_depth').
        score: 0.0–``max_score`` numeric score. 0.0 when unsupported.
        max_score: Maximum attainable score (default 100.0).
        confidence: 0.0–1.0 confidence in the score.
        confidence_level: One of :data:`VERIFICATION_LEVELS`.
        reasoning: Justification for the score, or :data:`CANNOT_VERIFY`.
        evidence: Resume-derived statements supporting the score.
    """
    name: str = ""
    score: float = 0.0
    max_score: float = 100.0
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class ProjectUnderstanding:
    """
    What the project actually is — purpose, problem, users, domain.

    Every free-text field is set to :data:`CANNOT_VERIFY` when the resume does
    not describe it, rather than being guessed.
    """
    purpose: str = ""
    problem_solved: str = ""
    intended_users: str = ""
    domain: str = ""
    project_type: str = ""
    business_value: str = ""
    confidence: float = 0.0
    confidence_level: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class ArchitectureFacet:
    """
    Assessment of one architectural area of the project.

    Attributes:
        area: 'frontend' | 'backend' | 'database' | 'system_design'.
        assessment: Narrative assessment, or :data:`CANNOT_VERIFY`.
        score / confidence / confidence_level / evidence: standard scored fields.
    """
    area: str = ""
    assessment: str = ""
    score: float = 0.0
    max_score: float = 100.0
    confidence: float = 0.0
    confidence_level: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class ComplexityAssessment:
    """
    Multi-dimensional complexity scoring. Each facet is an independent
    :class:`ScoredDimension` so the report never collapses complexity into a
    single shallow label.
    """
    overall: ScoredDimension = field(default_factory=lambda: ScoredDimension(name="overall"))
    backend: ScoredDimension = field(default_factory=lambda: ScoredDimension(name="backend"))
    frontend: ScoredDimension = field(default_factory=lambda: ScoredDimension(name="frontend"))
    database: ScoredDimension = field(default_factory=lambda: ScoredDimension(name="database"))
    system_design: ScoredDimension = field(default_factory=lambda: ScoredDimension(name="system_design"))
    integration: ScoredDimension = field(default_factory=lambda: ScoredDimension(name="integration"))
    deployment: ScoredDimension = field(default_factory=lambda: ScoredDimension(name="deployment"))


@dataclass
class TechnologyUsage:
    """
    Depth-of-use analysis for a single technology genuinely evidenced in the
    project (never inferred from a bare mention).

    Attributes:
        technology: Technology / language / tool name.
        usage_depth_score: 0.0–``max_score`` depth of demonstrated use.
        sophistication: Short label of how sophisticated the usage is.
        demonstrated_understanding: What the evidence shows the candidate grasps,
            or :data:`CANNOT_VERIFY`.
        confidence / confidence_level / reasoning / evidence: standard fields.
    """
    technology: str = ""
    usage_depth_score: float = 0.0
    max_score: float = 100.0
    sophistication: str = ""
    demonstrated_understanding: str = ""
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class Competency:
    """A demonstrated engineering competency with its score and evidence."""
    name: str = ""
    score: float = 0.0
    max_score: float = 100.0
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class SkillEvidenceItem:
    """
    Mapping of a single skill to how strongly the project evidences it.

    Attributes:
        skill: Skill name.
        status: :data:`SKILL_CLAIMED` | :data:`SKILL_DEMONSTRATED` |
            :data:`SKILL_VERIFIED` | :data:`SKILL_UNVERIFIED`.
        confidence / reasoning / evidence: standard fields.
    """
    skill: str = ""
    status: str = SKILL_UNVERIFIED
    confidence: float = 0.0
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class SkillEvidenceMap:
    """
    The Claimed / Demonstrated / Verified / Unverified skill mapping.

    ``claimed`` / ``demonstrated`` / ``verified`` / ``unverified`` are quick
    name lists; ``items`` carries the per-skill detail and evidence.
    """
    claimed: List[str] = field(default_factory=list)
    demonstrated: List[str] = field(default_factory=list)
    verified: List[str] = field(default_factory=list)
    unverified: List[str] = field(default_factory=list)
    items: List[SkillEvidenceItem] = field(default_factory=list)


@dataclass
class TechnicalMaturity:
    """
    Technical maturity classification for the project.

    Attributes:
        classification: One of :data:`MATURITY_TIERS`.
        score / confidence / confidence_level / reasoning / evidence: standard.
    """
    classification: str = ""
    score: float = 0.0
    max_score: float = 100.0
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class AssessedPoint:
    """
    A single strength, weakness, or risk — always with reasoning and evidence.
    """
    statement: str = ""
    reasoning: str = ""
    finding_type: str = ""
    confidence: float = 0.0
    confidence_level: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class MissingEvidenceItem:
    """
    An aspect that a thorough technical assessment would expect, but which the
    resume does not substantiate.

    Attributes:
        aspect: The missing aspect (e.g. 'testing strategy', 'deployment').
        description: What is missing / why it matters.
        impact: How the absence limits the assessment.
    """
    aspect: str = ""
    description: str = ""
    impact: str = ""


@dataclass
class ExecutiveAssessment:
    """Concise executive-level technical summary of the project."""
    overall_impression: str = ""
    demonstrates: List[str] = field(default_factory=list)
    does_not_demonstrate: List[str] = field(default_factory=list)
    strongest_signals: List[str] = field(default_factory=list)
    weakest_signals: List[str] = field(default_factory=list)
    overall_confidence: float = 0.0
    confidence_level: str = ""


@dataclass
class ProjectIntelligenceReport:
    """
    The comprehensive, evidence-based intelligence profile for ONE project.

    This is the permanent artifact Phase 3.7 produces and downstream engines
    (Skill, Internship, Readiness, Career-Fit, Resume Intelligence Aggregator)
    consume without re-analyzing.

    Notes on ``hiring_signal``:
        A 0–100 :class:`ScoredDimension`. It is explicitly **NOT** a hiring
        recommendation — it measures *how much hiring-relevant technical
        evidence the project provides*. Like every scored dimension it carries
        score + confidence + reasoning + evidence.

    Attributes:
        project_title: Title of the analyzed project.
        source_project: The :class:`ProjectEvidence` this report was built from.
        understanding: What the project is.
        architecture: Per-area architecture facets (frontend/backend/db/system).
        complexity: Multi-dimensional complexity scoring.
        engineering_depth: Depth-of-engineering scored dimension.
        technology_usage: Per-technology depth analysis.
        competencies: Demonstrated competencies with scores.
        skill_evidence: Claimed/Demonstrated/Verified/Unverified skill mapping.
        industry_relevance: Industry-relevance scored dimension.
        technical_maturity: Maturity classification.
        evidence_strength: How strong the supporting evidence is overall.
        hiring_signal: Hiring-relevant technical-evidence measure (0–100).
        strengths / weaknesses / risks: Evidence-backed assessed points.
        missing_evidence: Aspects the resume does not substantiate.
        executive_assessment: Executive-level technical summary.
        overall_confidence: 0.0–1.0 confidence across the whole report.
        overall_confidence_level: One of :data:`VERIFICATION_LEVELS`.
        caveats: Free-form caveats limiting the assessment.
    """
    project_title: str = ""
    source_project: Optional[ProjectEvidence] = None
    
    # Phase 3.12: Domain Intelligence Fields
    primary_domain: str = ""
    secondary_domains: List[str] = field(default_factory=list)
    domain_confidence: float = 0.0
    domain_signals: List[str] = field(default_factory=list)
    placement_signals: Dict[str, float] = field(default_factory=dict)
    project_tier: str = ""
    
    understanding: ProjectUnderstanding = field(default_factory=ProjectUnderstanding)
    architecture: List[ArchitectureFacet] = field(default_factory=list)
    complexity: ComplexityAssessment = field(default_factory=ComplexityAssessment)
    engineering_depth: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="engineering_depth")
    )
    technology_usage: List[TechnologyUsage] = field(default_factory=list)
    competencies: List[Competency] = field(default_factory=list)
    skill_evidence: SkillEvidenceMap = field(default_factory=SkillEvidenceMap)
    industry_relevance: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="industry_relevance")
    )
    technical_maturity: TechnicalMaturity = field(default_factory=TechnicalMaturity)
    evidence_strength: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="evidence_strength")
    )
    hiring_signal: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="hiring_signal")
    )
    strengths: List[AssessedPoint] = field(default_factory=list)
    weaknesses: List[AssessedPoint] = field(default_factory=list)
    missing_evidence: List[MissingEvidenceItem] = field(default_factory=list)
    risks: List[AssessedPoint] = field(default_factory=list)
    executive_assessment: ExecutiveAssessment = field(default_factory=ExecutiveAssessment)
    overall_confidence: float = 0.0
    overall_confidence_level: str = ""
    caveats: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Container
# ---------------------------------------------------------------------------


@dataclass
class ProjectAnalysisResult:
    """
    Container for all project findings extracted from a resume.

    Attributes:
        projects: List of extracted project evidence objects (Phase 3.5 layer).
        total_projects_count: Total number of valid projects identified.
        reports: Deep per-project intelligence reports (Phase 3.7 layer). Empty
            when analysis has not run (or produced nothing), which keeps this
            container backward-compatible with pure-extraction callers.
    """
    projects: List[ProjectEvidence] = field(default_factory=list)
    total_projects_count: int = 0
    reports: List[ProjectIntelligenceReport] = field(default_factory=list)
