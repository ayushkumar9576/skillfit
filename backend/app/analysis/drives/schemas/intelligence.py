"""
app/analysis/drives/schemas/intelligence.py
--------------------------------------------
Drive Intelligence Pydantic Schema — Phase 4.3.

This module defines the complete, strongly-typed intelligence taxonomy that
every Drive Intelligence snapshot must conform to.

Architecture principles enforced here:
    1. Evidence-backed  — every artifact carries a non-empty evidence list.
    2. Taxonomy-bounded — all categories are bounded to Enum members.
    3. Versioned        — INTELLIGENCE_SCHEMA_VERSION is stamped on every profile.
    4. LLM-safe         — designed to be the ``response_schema`` passed directly
                          to BaseLLMProvider.complete_structured(); Pydantic
                          validation is the first defence layer.
    5. Phase-5-ready    — importance, confidence, strength fields are preserved
                          as typed scalars (not free-text) for future ML use.

Schema versioning:
    Bump INTELLIGENCE_SCHEMA_VERSION whenever any field is added, removed, or
    renamed. Snapshots persist this value so deserialization code can route
    to the correct backwards-compatible model in future phases.

    Current: v1.0
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import (
    BehavioralCompetencyType,
    DriveConfidenceLevel,
    EvidenceSection,
    EvidenceType,
    HiringSignalType,
    ImportanceLevel,
    ProfessionalDomainType,
    QualificationType,
    RiskType,
    SelectionRoundType,
    SuccessIndicatorStrength,
    SuccessIndicatorType,
    TechnicalCompetencyType,
    TechnologyCategory,
)

# ---------------------------------------------------------------------------
# Schema version — bump this on any breaking or additive schema change
# ---------------------------------------------------------------------------

INTELLIGENCE_SCHEMA_VERSION: str = "v1.0"


# ===========================================================================
# 1. Evidence (reusable base — attached to every intelligence artifact)
# ===========================================================================


class Evidence(BaseModel):
    """
    A single traceable evidence snippet extracted from the JD.

    Every intelligence artifact must carry ≥1 Evidence item.
    This is the fundamental unit of explainability — it answers:
    "Why was this conclusion generated?"

    Attributes:
        source_text:    The exact verbatim quote or close paraphrase from the
                        normalized JD content that supports this artifact.
        evidence_type:  Whether this was explicitly stated or inferred.
        confidence:     How certain the engine is about this interpretation.
        source_section: Which part of the JD this evidence came from.
    """

    source_text: str = Field(
        ...,
        min_length=15,
        description="Verbatim or close-paraphrase quote from the JD.",
    )
    evidence_type: EvidenceType = Field(
        ...,
        description="Explicit requirement, responsibility, qualification, or inferred signal.",
    )
    confidence: DriveConfidenceLevel = Field(
        ...,
        description="Engine confidence in this evidence interpretation.",
    )
    source_section: EvidenceSection = Field(
        default=EvidenceSection.other,
        description="JD section where this evidence was found.",
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 2. Technology Intelligence
# ===========================================================================


class TechnologyIntelligence(BaseModel):
    """
    A single technology requirement inferred from the JD.

    Design:
        - ``name`` is the canonical technology name (e.g. "Python", "PostgreSQL").
          The Governance Layer normalizes synonyms ("Node.js" → "Node.js") and
          deduplicates before snapshot creation.
        - ``category`` is taxonomy-bounded to TechnologyCategory.
        - ``importance`` drives Phase 5 matching weight.
        - ``is_mandatory`` strictly separates required skills from preferred skills.
        - ``evidence`` must be non-empty (Governance Layer enforces this).
    """

    name: str = Field(..., min_length=1, description="Canonical technology name.")
    category: TechnologyCategory = Field(..., description="Technology classification.")
    importance: ImportanceLevel = Field(
        ..., description="How critical this technology is for the role."
    )
    confidence: DriveConfidenceLevel = Field(
        ..., description="Engine confidence in this technology requirement."
    )
    is_mandatory: Optional[bool] = Field(
        default=None, 
        description="True if required, False if preferred. None for historical snapshots."
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence supporting this technology requirement."
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 3. Professional Domain Intelligence
# ===========================================================================


class ProfessionalDomainIntelligence(BaseModel):
    """
    Overarching business domain or role family inferred from the JD.
    """

    domain: ProfessionalDomainType = Field(
        ..., description="Domain classification (e.g. SOFTWARE_ENGINEERING, DATA)."
    )
    confidence: DriveConfidenceLevel = Field(
        ..., description="Engine confidence in this domain inference."
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence supporting this domain."
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 4. Competency Intelligence (separated into Technical & Behavioral domains)
# ===========================================================================


class TechnicalCompetencyIntelligence(BaseModel):
    """
    A technical hard-skill competency expected from candidates.

    Separated from behavioral competencies so Phase 5 can apply different
    matching algorithms: technical gaps are penalized at the eligibility
    layer; behavioral gaps are penalized at the ranking layer.
    """

    competency: TechnicalCompetencyType = Field(
        ..., description="Technical competency type from the taxonomy."
    )
    importance: ImportanceLevel = Field(
        ..., description="How critical this competency is."
    )
    confidence: DriveConfidenceLevel = Field(
        ..., description="Confidence in this competency inference."
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence for this competency requirement."
    )

    model_config = {"use_enum_values": True}


class BehavioralCompetencyIntelligence(BaseModel):
    """
    A behavioral soft-skill competency expected from candidates.

    Phase 5 behavioral scoring models may weight these differently than
    technical competencies (e.g., leadership-focused roles).
    """

    competency: BehavioralCompetencyType = Field(
        ..., description="Behavioral competency type from the taxonomy."
    )
    importance: ImportanceLevel = Field(
        ..., description="How critical this behavioral trait is."
    )
    confidence: DriveConfidenceLevel = Field(
        ..., description="Confidence in this behavioral competency inference."
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence for this behavioral expectation."
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 5. Qualification Intelligence
# ===========================================================================


class QualificationIntelligence(BaseModel):
    """
    An eligibility constraint extracted from the JD.

    ``is_mandatory`` distinguishes hard filters (e.g., "CGPA >= 7.5 required")
    from soft preferences (e.g., "preferred: CSE branch"), enabling Phase 5
    to gate candidates before ranking.

    ``expected_value`` is a free-text string to accommodate diverse formats:
    - CGPA: "7.5 or above"
    - Branch: "CSE, IT, ECE"
    - Graduation Year: "2025, 2026"
    """

    qualification_type: QualificationType = Field(
        ..., description="Type of eligibility constraint."
    )
    expected_value: str = Field(
        ..., min_length=1, description="The required/expected value for this qualification."
    )
    is_mandatory: bool = Field(
        ...,
        description="True = hard filter (eliminates ineligible candidates). "
                    "False = preference (used in ranking, not elimination).",
    )
    confidence: DriveConfidenceLevel = Field(
        ..., description="Confidence in this qualification extraction."
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence for this eligibility constraint."
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 6. Hiring Signal Intelligence
# ===========================================================================


class HiringSignal(BaseModel):
    """
    An implicit hiring preference inferred from JD language and emphasis.

    These are never explicitly stated — they emerge from the vocabulary,
    structure, and emphasis the JD uses (e.g., heavy DSA language → DSA_FOCUSED).

    ``importance`` captures how strongly this signal dominates the JD.
    Phase 5 uses signals to cluster drives by hiring culture and preference.
    """

    signal: HiringSignalType = Field(
        ..., description="The implicit hiring preference signal type."
    )
    importance: ImportanceLevel = Field(
        ..., description="How dominant this signal is in the drive."
    )
    confidence: DriveConfidenceLevel = Field(
        ..., description="Confidence in this inferred signal."
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence supporting this hiring signal."
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 7. Role Expectation Intelligence
# ===========================================================================


class RoleExpectation(BaseModel):
    """
    An actionable responsibility or expectation for the role.

    Captures what candidates will *actually do* in the job.
    Phase 5 uses role expectations to match against project/internship evidence
    in the candidate profile.

    ``expectation`` is free-text because responsibilities are too varied to
    enumerate in a taxonomy (unlike categories which are fixed).
    """

    expectation: str = Field(
        ..., min_length=5, description="Described responsibility or expectation."
    )
    importance: ImportanceLevel = Field(
        ..., description="How central this expectation is to the role."
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence from the JD for this expectation."
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 8. Selection Process Intelligence
# ===========================================================================


class SelectionProcessIntelligence(BaseModel):
    """
    A single round in the hiring selection process.

    First-class intelligence object because the selection funnel directly
    impacts candidate preparation strategy. Phase 5 readiness modules will
    match candidates to their weakest stage types.

    ``round_name`` is the company's label (e.g., "HackerRank OA", "L1 Tech").
    ``round_type`` is the normalized taxonomy category.
    ``importance`` reflects how eliminatory this round typically is.
    """

    round_name: str = Field(
        ..., min_length=1, description="Company's label for this selection round."
    )
    round_type: SelectionRoundType = Field(
        ..., description="Normalized round type from the taxonomy."
    )
    importance: ImportanceLevel = Field(
        ..., description="How eliminatory this round is."
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence this round exists."
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 10. Risk Intelligence
# ===========================================================================


class RiskIntelligence(BaseModel):
    """
    A structural risk associated with this drive.

    Helps placement officers identify drives that may yield low selection
    rates or require exceptional candidate preparation. Phase 5 surfaces
    risk-weighted recommendations.

    ``severity`` uses ImportanceLevel:
        LOW      → Minor concern; most eligible candidates unaffected.
        MEDIUM   → Notable challenge; warrants preparation guidance.
        HIGH     → Significant barrier; expect high dropout.
        CRITICAL → Only exceptional candidates likely to clear.
    """

    risk: RiskType = Field(..., description="Risk type from the taxonomy.")
    severity: ImportanceLevel = Field(
        ..., description="Severity of this risk for candidate success."
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence supporting this risk identification."
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 9. Success Indicator Intelligence
# ===========================================================================


class SuccessIndicator(BaseModel):
    """
    A candidate trait or experience that correlates with success in this drive.

    Distinct from QualificationIntelligence (eligibility) and HiringSignal
    (implicit preferences). SuccessIndicators are what the drive *rewards*.

    ``strength`` is the primary Phase 5 ranking signal:
        REQUIRED  → Without this, candidates are unlikely to clear selection.
        PREFERRED → Candidates with this have a strong competitive advantage.
        BONUS     → Minor ranking boost; tiebreaker between equal candidates.
    """

    indicator: SuccessIndicatorType = Field(
        ..., description="The success indicator type from the taxonomy."
    )
    strength: SuccessIndicatorStrength = Field(
        ...,
        description="How strongly this indicator influences success. "
                    "Differs from importance: importance measures eligibility criticality, "
                    "strength measures competitive differentiation.",
    )
    evidence: List[Evidence] = Field(
        ..., min_length=1, description="Evidence that this indicator matters for the drive."
    )

    model_config = {"use_enum_values": True}


# ===========================================================================
# 10. DriveIntelligenceProfile — Aggregate Root
# ===========================================================================


class DriveIntelligenceProfile(BaseModel):
    """
    The complete structured intelligence extracted from a placement drive JD.

    This is the output contract of the DriveIntelligenceEngine (Phase 4.3)
    and the input contract of the Phase 5 matching and ranking systems.

    Design guarantees:
        - All lists may be empty (a JD may not mention selection rounds).
        - All individual artifacts carry ≥1 evidence item (enforced by Pydantic
          and the Governance Layer).
        - ``intelligence_schema_version`` enables backwards-compatible
          deserialization as the schema evolves in future phases.

    Snapshot storage:
        This object is serialized to JSON and stored in
        DriveSnapshot.intelligence_payload. The ``intelligence_schema_version``
        is also denormalized into a dedicated column for fast querying.
    """

    # Schema version — stamped on every profile for safe future evolution
    intelligence_schema_version: str = Field(
        default=INTELLIGENCE_SCHEMA_VERSION,
        description="Schema version of this output.",
    )

    domain: Optional[ProfessionalDomainIntelligence] = Field(
        default=None, description="The overarching professional domain of the role."
    )

    technologies: List[TechnologyIntelligence] = Field(
        default_factory=list, description="All specific tools, languages, and frameworks."
    )
    technical_competencies: List[TechnicalCompetencyIntelligence] = Field(
        default_factory=list,
        description="Technical hard-skill competencies expected from candidates.",
    )
    behavioral_competencies: List[BehavioralCompetencyIntelligence] = Field(
        default_factory=list,
        description="Behavioral soft-skill competencies expected from candidates.",
    )
    qualifications: List[QualificationIntelligence] = Field(
        default_factory=list,
        description="Eligibility constraints (CGPA, branch, graduation year, etc.).",
    )
    hiring_signals: List[HiringSignal] = Field(
        default_factory=list,
        description="Implicit hiring preference signals inferred from the JD.",
    )
    role_expectations: List[RoleExpectation] = Field(
        default_factory=list,
        description="Actionable responsibilities and expectations for the role.",
    )
    selection_process: List[SelectionProcessIntelligence] = Field(
        default_factory=list,
        description="Ordered selection rounds in the hiring funnel.",
    )
    risks: List[RiskIntelligence] = Field(
        default_factory=list,
        description="Structural risks associated with this drive.",
    )
    success_indicators: List[SuccessIndicator] = Field(
        default_factory=list,
        description="Candidate traits that correlate with success in this drive.",
    )

    model_config = {"use_enum_values": True}

    @model_validator(mode="after")
    def _validate_minimum_intelligence(self) -> "DriveIntelligenceProfile":
        """
        Enforce that the profile carries at least some intelligence.
        A completely empty profile indicates a catastrophic LLM or prompt failure.
        """
        total_artifacts = (
            len(self.technologies)
            + len(self.technical_competencies)
            + len(self.qualifications)
            + len(self.role_expectations)
        )
        if total_artifacts == 0:
            raise ValueError(
                "DriveIntelligenceProfile contains zero intelligence artifacts. "
                "The LLM likely returned an empty or malformed response. "
                "Check prompt version and JD content."
            )
        return self

    def to_snapshot_dict(self) -> dict:
        """
        Serialize to a plain dict suitable for JSONB storage in DriveSnapshot.

        Returns enum values as strings (not enum objects) for JSON compatibility.
        """
        return self.model_dump(mode="json")
