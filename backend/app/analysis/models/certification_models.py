"""
app/analysis/models/certification_models.py
-------------------------------------------
Certification and credential domain models for SkillFit Phase 3.5 and 3.9.

Two layers live here:

    1. Extraction layer (Phase 3.5) — ``CertificationEvidence`` and the
       ``CertificationAnalysisResult`` container. Describes *what was found* in
       the resume text.

    2. Intelligence layer (Phase 3.9) — ``CertificationIntelligenceReport`` and its
       supporting structures. A highly token-optimized, evidence-backed assessment
       focusing ONLY on hiring signals, recognition, and skill signaling.

Design Rules:
    - Pure standard library dataclasses only.
    - Zero framework dependencies.
    - Fully serializable via ``dataclasses.asdict()``.
    - Plain-string tiers.
    - Highly constrained dimensions to prevent token bloat and hallucination.

Consumed by:
    - Phase 3.9: Certification Analysis Engine
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

#: Canonical sentinel emitted whenever an assessment cannot be substantiated.
CANNOT_VERIFY: str = "Cannot be verified from available evidence."

# Provider Tiers
PROVIDER_HIGH: str = "high"
PROVIDER_MEDIUM: str = "medium"
PROVIDER_LOW: str = "low"
PROVIDER_UNKNOWN: str = "unknown"


# ---------------------------------------------------------------------------
# Extraction layer (Phase 3.5)
# ---------------------------------------------------------------------------

@dataclass
class CertificationEvidence:
    """
    Represents a verified professional certification, license, or accredited course.

    Attributes:
        certification_name: Title of the certification (e.g. 'AWS Certified Solutions Architect').
        issuer: Organization issuing the certification (e.g. 'Amazon Web Services', 'Coursera').
        issue_date: Date or year obtained.
        expiry_date: Expiration date if applicable.
        credential_id: Official license or certification verification ID.
        credential_url: Public credential verification link.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    certification_name: str
    issuer: str
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Intelligence layer (Phase 3.9) — supporting structures
# ---------------------------------------------------------------------------

@dataclass
class ScoredDimension:
    """A single evidence-backed scored dimension (used for hiring signal, evidence strength, etc)."""
    name: str = ""
    score: float = 0.0
    max_score: float = 100.0
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    classification: Optional[str] = None
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class SkillSignal:
    """A skill reasonably implied by the certification."""
    name: str = ""
    confidence: float = 0.0
    confidence_level: str = ""
    reasoning: str = ""
    evidence: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class ExecutiveAssessment:
    """Concise executive-level summary of the certification."""
    overall_value: str = ""
    strongest_signal: str = ""
    primary_limitation: str = ""


@dataclass
class CertificationIntelligenceReport:
    """
    The compact, evidence-backed intelligence profile for ONE certification.
    """
    certification_name: str = ""
    source_certification: Optional[CertificationEvidence] = None
    
    # Evaluated deterministically
    provider_tier: str = PROVIDER_UNKNOWN
    
    # LLM evaluated (influenced by deterministic signals)
    certification_recognition: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="certification_recognition")
    )
    skill_signals: List[SkillSignal] = field(default_factory=list)
    industry_relevance: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="industry_relevance")
    )
    hiring_signal: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="hiring_signal")
    )
    evidence_strength: ScoredDimension = field(
        default_factory=lambda: ScoredDimension(name="evidence_strength")
    )
    executive_assessment: ExecutiveAssessment = field(default_factory=ExecutiveAssessment)
    overall_confidence: float = 0.0
    confidence_level: str = ""
    caveats: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Container
# ---------------------------------------------------------------------------

@dataclass
class CertificationAnalysisResult:
    """
    Container for all certification findings extracted from a resume.

    Attributes:
        certifications: List of certification evidence objects.
        reports: List of certification intelligence reports (populated in Phase 3.9).
        total_certifications_count: Total count of certifications identified.
    """
    certifications: List[CertificationEvidence] = field(default_factory=list)
    reports: List[CertificationIntelligenceReport] = field(default_factory=list)
    total_certifications_count: int = 0
