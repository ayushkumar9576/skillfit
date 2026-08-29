"""
app/analysis/models/internship_models.py
----------------------------------------
Internship analysis domain models for SkillFit Phase 3.5 & 3.8.

Two layers live here:

    1. Extraction layer (Phase 3.5) — ``InternshipEvidence`` and the
       ``InternshipAnalysisResult`` container. These describe *what was found* in
       the resume text with light extraction confidence.

    2. Intelligence layer (Phase 3.8) — ``InternshipIntelligenceReport`` and its
       supporting structures. These describe *the deep, evidence-based
       technical assessment* of a single internship: multi-dimensional understanding,
       technical depth, ownership, collaboration, workplace maturity, etc.

Design Rules (Phase 3.5 & 3.8 purity, preserved here):
    - Pure standard library dataclasses only.
    - Zero framework dependencies (no SQLAlchemy, FastAPI, Pydantic, or OpenAI).
    - Fully serializable via ``dataclasses.asdict()``.
    - Classification / confidence tiers are stored as plain strings.

Consumed by:
    - Phase 3.8: Internship Analysis Engine
    - Phase 3.10: Evidence-Based Skill Engine
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence

# ---------------------------------------------------------------------------
# Evidence-based vocabulary (plain-string tiers — no enum coupling)
# ---------------------------------------------------------------------------

from enum import Enum

class InternshipEvidenceType(str, Enum):
    DIRECT_WORK = "DIRECT_WORK"
    DIRECT_RESULT = "DIRECT_RESULT"
    DIRECT_RESPONSIBILITY = "DIRECT_RESPONSIBILITY"
    CLAIMED = "CLAIMED"

class InternshipDemonstrationLevel(str, Enum):
    CLAIMED = "CLAIMED"
    ASSISTED = "ASSISTED"
    EXECUTED = "EXECUTED"
    OWNED = "OWNED"
    LED = "LED"

class InternshipTier(str, Enum):
    EXPOSURE = "EXPOSURE"
    CONTRIBUTOR = "CONTRIBUTOR"
    OWNER = "OWNER"
    HIGH_IMPACT = "HIGH_IMPACT"

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

# Skill-evidence mapping statuses.
SKILL_CLAIMED: str = "claimed"
SKILL_DEMONSTRATED: str = "demonstrated"
SKILL_VERIFIED: str = "verified"
SKILL_UNVERIFIED: str = "unverified"

# ---------------------------------------------------------------------------
# Extraction layer (Phase 3.5)
# ---------------------------------------------------------------------------


@dataclass
class InternshipEvidence:
    """
    Represents an internship experience extracted from resume content.

    Attributes:
        organization: Company or institution name.
        role: Internship title (e.g. 'Software Engineer Intern', 'Data Science Intern').
        duration: Date range or timeframe of the internship.
        location: Geographic location or 'Remote'.
        description: Summary of work and core responsibilities.
        technologies_used: List of technical tools and frameworks applied.
        achievements: Quantifiable outcomes or key deliverables accomplished.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    organization: str
    role: str
    duration: Optional[str] = None
    location: Optional[str] = None
    description: str = ""
    technologies_used: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Intelligence layer (Phase 3.8) — supporting structures
# ---------------------------------------------------------------------------


@dataclass
class ScoredDimension:
    """
    A single evidence-backed scored dimension.
    """
    name: str = ""
    score: float = 0.0
    max_score: float = 100.0
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class InternshipUnderstanding:
    """What the internship actually is."""
    purpose: str = ""
    domain: str = ""
    company_type: str = ""
    team_function: str = ""
    role_objective: str = ""
    confidence: float = 0.0
    confidence_level: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class WorkplaceMaturity:
    """Classification/score capturing exposure to production systems, etc."""
    classification: str = ""
    score: float = 0.0
    max_score: float = 100.0
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class OwnershipClassification:
    """Classification of ownership (observer, contributor, owner, lead_contributor)."""
    classification: str = ""
    score: float = 0.0
    max_score: float = 100.0
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class TechnologyUsage:
    """Depth-of-use analysis for a single technology genuinely evidenced."""
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
    """A demonstrated competency with its score and evidence."""
    name: str = ""
    score: float = 0.0
    max_score: float = 100.0
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class SkillEvidenceItem:
    """Mapping of a single skill to how strongly the internship evidences it."""
    skill: str = ""
    status: str = SKILL_UNVERIFIED
    confidence: float = 0.0
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class SkillEvidenceMap:
    """The Claimed / Demonstrated / Verified / Unverified skill mapping."""
    claimed: List[str] = field(default_factory=list)
    demonstrated: List[str] = field(default_factory=list)
    verified: List[str] = field(default_factory=list)
    unverified: List[str] = field(default_factory=list)
    items: List[SkillEvidenceItem] = field(default_factory=list)


@dataclass
class AssessedPoint:
    """A single strength, weakness, or risk."""
    statement: str = ""
    reasoning: str = ""
    confidence: float = 0.0
    confidence_level: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class MissingEvidenceItem:
    """An aspect that the resume does not substantiate."""
    aspect: str = ""
    description: str = ""
    impact: str = ""


@dataclass
class ExecutiveAssessment:
    """Concise executive-level technical summary of the internship."""
    overall_impression: str = ""
    demonstrates: List[str] = field(default_factory=list)
    does_not_demonstrate: List[str] = field(default_factory=list)
    strongest_signals: List[str] = field(default_factory=list)
    weakest_signals: List[str] = field(default_factory=list)
    overall_confidence: float = 0.0
    confidence_level: str = ""


@dataclass
class InternshipIntelligenceReport:
    """
    The comprehensive, evidence-based intelligence profile for ONE internship.
    """
    internship_role: str = ""
    internship_organization: str = ""
    source_internship: Optional[InternshipEvidence] = None
    
    # Phase 3.12: Domain Intelligence Fields
    primary_domain: str = ""
    secondary_domains: List[str] = field(default_factory=list)
    domain_confidence: float = 0.0
    industry_exposure_level: str = ""
    internship_tier: str = ""
    
    understanding: InternshipUnderstanding = field(default_factory=InternshipUnderstanding)
    technical_depth: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="technical_depth")
    )
    engineering_ownership: OwnershipClassification = field(default_factory=OwnershipClassification)
    collaboration_exposure: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="collaboration_exposure")
    )
    impact_analysis: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="impact_analysis")
    )
    production_exposure: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="production_exposure")
    )
    software_engineering_practices: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="software_engineering_practices")
    )
    technology_usage: List[TechnologyUsage] = field(default_factory=list)
    competencies: List[Competency] = field(default_factory=list)
    skill_evidence: SkillEvidenceMap = field(default_factory=SkillEvidenceMap)
    industry_readiness: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="industry_readiness")
    )
    hiring_signal: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="hiring_signal")
    )
    internship_quality: str = ""  # basic, average, strong, exceptional
    workplace_maturity: WorkplaceMaturity = field(default_factory=WorkplaceMaturity)
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
class InternshipAnalysisResult:
    """
    Container for all internship findings extracted from a resume.

    Attributes:
        internships: List of extracted internship evidence objects (Phase 3.5 layer).
        total_internships_count: Total count of internships identified.
        reports: Deep per-internship intelligence reports (Phase 3.8 layer).
    """
    internships: List[InternshipEvidence] = field(default_factory=list)
    total_internships_count: int = 0
    reports: List[InternshipIntelligenceReport] = field(default_factory=list)
