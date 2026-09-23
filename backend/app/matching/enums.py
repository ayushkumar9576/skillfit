"""
app/matching/enums.py
---------------------
Matching-domain enumerations for Phase 5 — Matching Intelligence.

Design Rules:
    - All enums inherit from (str, enum.Enum) for JSON-serialization safety.
    - All values use UPPER_CASE strings, consistent with CanonicalCompetencyType
      and ProfessionalDomainType in app.core.enums.
    - No cross-imports from app.matching sub-modules to keep this file
      import-safe as a leaf dependency.

These enums describe *matching concepts* — they are distinct from intelligence
enums (DemonstrationLevel, ImportanceLevel) which describe extracted artifacts.

Phase 5.1 — Foundation Only.
"""

import enum


class MatchDimension(str, enum.Enum):
    """
    The six scoring dimensions of the Phase 5 Matching Engine.

    Each dimension maps to a section of CandidateIntelligenceProfile versus
    the corresponding section of DriveIntelligenceProfile:

        TECHNOLOGY   ↔  candidate.technologies   vs  drive.technologies
        COMPETENCY   ↔  candidate.competencies   vs  drive.technical_competencies
        DOMAIN       ↔  candidate.domains        vs  drive.domain
        SIGNAL       ↔  candidate.engineering_signals  vs  drive.hiring_signals
        PROJECT      ↔  candidate.project_sophistication vs drive.success_indicators
        BEHAVIORAL   ↔  candidate.ownership_signals vs drive.behavioral_competencies

    Phase 5.2 will implement the scoring algorithm for each dimension.
    Phase 5.1 uses this enum only for type-safe labeling of DimensionScore records.
    """
    TECHNOLOGY = "TECHNOLOGY"
    COMPETENCY = "COMPETENCY"
    DOMAIN     = "DOMAIN"
    SIGNAL     = "SIGNAL"
    PROJECT    = "PROJECT"
    BEHAVIORAL = "BEHAVIORAL"


class MatchTier(str, enum.Enum):
    """
    Human-readable tier label derived from MatchScore.overall_score.

    Tier boundaries are defined in app.matching.models.result and applied
    deterministically — the LLM never assigns a tier.

    Ordering (weakest → strongest):
        WEAK < PARTIAL < MODERATE < STRONG < EXCELLENT
    """
    WEAK      = "WEAK"
    PARTIAL   = "PARTIAL"
    MODERATE  = "MODERATE"
    STRONG    = "STRONG"
    EXCELLENT = "EXCELLENT"

    @classmethod
    def from_score(cls, score: float) -> "MatchTier":
        """
        Derive a MatchTier from a normalized score in [0.0, 1.0].

        Boundaries:
            [0.00, 0.40) → WEAK
            [0.40, 0.55) → PARTIAL
            [0.55, 0.70) → MODERATE
            [0.70, 0.85) → STRONG
            [0.85, 1.00] → EXCELLENT

        Args:
            score: Normalized overall match score. Must be in [0.0, 1.0].

        Raises:
            ValueError: If score is outside [0.0, 1.0].
        """
        if not (0.0 <= score <= 1.0):
            raise ValueError(
                f"Score must be in [0.0, 1.0], got {score!r}."
            )
        if score >= 0.85:
            return cls.EXCELLENT
        if score >= 0.70:
            return cls.STRONG
        if score >= 0.55:
            return cls.MODERATE
        if score >= 0.40:
            return cls.PARTIAL
        return cls.WEAK


class GapSeverity(str, enum.Enum):
    """
    Severity of a MatchGap — how significantly a missing capability
    hurts the candidate's overall match score for a drive.

    Determined by the scoring engine based on the drive's ImportanceLevel
    for the missing item:
        ImportanceLevel.CRITICAL → GapSeverity.CRITICAL
        ImportanceLevel.HIGH     → GapSeverity.HIGH
        ImportanceLevel.MEDIUM   → GapSeverity.MEDIUM
        ImportanceLevel.LOW      → GapSeverity.LOW

    Phase 5.2 will implement the derivation logic.
    """
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"
