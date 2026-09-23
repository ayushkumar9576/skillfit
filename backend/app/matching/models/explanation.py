"""
app/matching/models/explanation.py
------------------------------------
Explainability models for Phase 5 — Matching Intelligence.

Design Rules:
    - Pure standard library dataclasses only.
    - Zero framework dependencies.
    - Fully serializable via dataclasses.asdict().
    - Every explanation object is backed by an evidence source
      (dimension, reasoning) so the UI can display verbatim justification.
    - Validation is strict: empty titles and malformed evidence are rejected.

Explainability Architecture:
    MatchStrength      — a positive alignment between candidate and drive
    MatchGap           — a missing or insufficient capability
    DimensionBreakdown — the score and narrative for one matching dimension
    MatchExplanation   — aggregate container for all of the above

Phase 5.1 — Foundation Only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.matching.enums import GapSeverity, MatchDimension


# ---------------------------------------------------------------------------
# Validation helpers (local, not exported)
# ---------------------------------------------------------------------------

def _require_non_empty_str(value: str, field_name: str) -> str:
    """
    Ensure a string is non-empty after stripping whitespace.

    Args:
        value:      The string to validate.
        field_name: Name of the field for error messages.

    Returns:
        The original (non-stripped) string if valid.

    Raises:
        TypeError:  If value is not a str.
        ValueError: If value is empty or only whitespace.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a str, got {type(value).__name__!r}."
        )
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty.")
    return value


# ---------------------------------------------------------------------------
# MatchStrength
# ---------------------------------------------------------------------------

@dataclass
class MatchStrength:
    """
    A single positive alignment between the candidate and the drive.

    Represents evidence that the candidate has a capability that the drive
    values. Strength objects are collected into MatchExplanation.strengths.

    Attributes:
        title:          Short, recruiter-facing label.
                        Example: "Strong Backend Development"
        dimension:      The MatchDimension this strength belongs to.
        description:    Detailed human-readable explanation.
                        Example: "Candidate has ARCHITECTED-level evidence for
                        Django and FastAPI, matching the drive's CRITICAL
                        backend requirement."
        candidate_evidence: Verbatim candidate evidence quote (from
                        IntelligenceEvidence.quote on the Candidate side).
                        Empty string if no specific quote is applicable.
        drive_evidence: Verbatim drive evidence quote (from Evidence.source_text
                        on the Drive side). Empty string if not applicable.
        impact_score:   Contribution of this strength to the overall score,
                        in [0.0, 1.0]. Computed by Phase 5.2 scoring engines.
    """
    title:              str
    dimension:          MatchDimension
    description:        str
    candidate_evidence: str = ""
    drive_evidence:     str = ""
    impact_score:       float = 0.0

    def __post_init__(self) -> None:
        """Validate required string fields and enum type."""
        _require_non_empty_str(self.title, "title")
        _require_non_empty_str(self.description, "description")

        if not isinstance(self.dimension, MatchDimension):
            raise TypeError(
                f"dimension must be a MatchDimension instance, "
                f"got {type(self.dimension).__name__!r}."
            )
        if not isinstance(self.candidate_evidence, str):
            raise TypeError("candidate_evidence must be a str.")
        if not isinstance(self.drive_evidence, str):
            raise TypeError("drive_evidence must be a str.")

        if not isinstance(self.impact_score, (int, float)):
            raise TypeError("impact_score must be numeric.")
        self.impact_score = float(self.impact_score)
        if not (0.0 <= self.impact_score <= 1.0):
            raise ValueError(
                f"impact_score must be in [0.0, 1.0], got {self.impact_score!r}."
            )

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON-safe API serialization."""
        return {
            "title":              self.title,
            "dimension":          self.dimension.value,
            "description":        self.description,
            "candidate_evidence": self.candidate_evidence,
            "drive_evidence":     self.drive_evidence,
            "impact_score":       self.impact_score,
        }


# ---------------------------------------------------------------------------
# MatchGap
# ---------------------------------------------------------------------------

@dataclass
class MatchGap:
    """
    A missing or insufficient capability relative to drive requirements.

    Represents a requirement in the drive that the candidate does not satisfy
    or satisfies only weakly. Gap objects are collected into
    MatchExplanation.gaps.

    Severity Mapping (applied by Phase 5.2):
        drive ImportanceLevel.CRITICAL → GapSeverity.CRITICAL
        drive ImportanceLevel.HIGH     → GapSeverity.HIGH
        drive ImportanceLevel.MEDIUM   → GapSeverity.MEDIUM
        drive ImportanceLevel.LOW      → GapSeverity.LOW

    Attributes:
        title:           Short, recruiter-facing label.
                         Example: "Missing: System Design"
        dimension:       The MatchDimension this gap belongs to.
        severity:        How significantly this gap hurts the match score.
        description:     Detailed human-readable explanation of the gap.
        drive_evidence:  Verbatim drive evidence showing this requirement.
        improvement_hint: Optional actionable suggestion for the candidate.
                         Never auto-generated by the LLM — derived
                         deterministically from the gap type by Phase 5.2.
    """
    title:            str
    dimension:        MatchDimension
    severity:         GapSeverity
    description:      str
    drive_evidence:   str = ""
    improvement_hint: str = ""

    def __post_init__(self) -> None:
        """Validate required string fields and enum types."""
        _require_non_empty_str(self.title, "title")
        _require_non_empty_str(self.description, "description")

        if not isinstance(self.dimension, MatchDimension):
            raise TypeError(
                f"dimension must be a MatchDimension instance, "
                f"got {type(self.dimension).__name__!r}."
            )
        if not isinstance(self.severity, GapSeverity):
            raise TypeError(
                f"severity must be a GapSeverity instance, "
                f"got {type(self.severity).__name__!r}."
            )
        if not isinstance(self.drive_evidence, str):
            raise TypeError("drive_evidence must be a str.")
        if not isinstance(self.improvement_hint, str):
            raise TypeError("improvement_hint must be a str.")

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON-safe API serialization."""
        return {
            "title":            self.title,
            "dimension":        self.dimension.value,
            "severity":         self.severity.value,
            "description":      self.description,
            "drive_evidence":   self.drive_evidence,
            "improvement_hint": self.improvement_hint,
        }


# ---------------------------------------------------------------------------
# DimensionBreakdown
# ---------------------------------------------------------------------------

@dataclass
class DimensionBreakdown:
    """
    A per-dimension summary combining the numeric score with narrative
    explanation for one matching dimension.

    Used in MatchExplanation.dimension_breakdown to provide dimension-level
    detail beyond just the score number.

    Attributes:
        dimension:     The MatchDimension this breakdown covers.
        raw_score:     The dimension's raw_score in [0.0, 1.0].
        weighted_score: The dimension's weighted contribution in [0.0, 1.0].
        strengths:     Strength objects for this dimension specifically.
        gaps:          Gap objects for this dimension specifically.
        narrative:     One-sentence summary of the dimension match.
                       Example: "Strong backend match; missing cloud experience."
    """
    dimension:      MatchDimension
    raw_score:      float
    weighted_score: float
    strengths:      List[MatchStrength] = field(default_factory=list)
    gaps:           List[MatchGap]      = field(default_factory=list)
    narrative:      str = ""

    def __post_init__(self) -> None:
        """Validate numeric fields and list element types."""
        if not isinstance(self.dimension, MatchDimension):
            raise TypeError(
                f"dimension must be a MatchDimension instance, "
                f"got {type(self.dimension).__name__!r}."
            )

        for attr, bound_name in [("raw_score", "raw_score"), ("weighted_score", "weighted_score")]:
            v = getattr(self, attr)
            if not isinstance(v, (int, float)):
                raise TypeError(f"{bound_name} must be numeric.")
            v = float(v)
            if not (0.0 <= v <= 1.0):
                raise ValueError(
                    f"{bound_name} must be in [0.0, 1.0], got {v!r}."
                )
            setattr(self, attr, v)

        if not isinstance(self.strengths, list):
            raise TypeError("strengths must be a list.")
        for i, s in enumerate(self.strengths):
            if not isinstance(s, MatchStrength):
                raise TypeError(
                    f"strengths[{i}] must be a MatchStrength instance, "
                    f"got {type(s).__name__!r}."
                )

        if not isinstance(self.gaps, list):
            raise TypeError("gaps must be a list.")
        for i, g in enumerate(self.gaps):
            if not isinstance(g, MatchGap):
                raise TypeError(
                    f"gaps[{i}] must be a MatchGap instance, "
                    f"got {type(g).__name__!r}."
                )

        if not isinstance(self.narrative, str):
            raise TypeError("narrative must be a str.")

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON-safe API serialization."""
        return {
            "dimension":      self.dimension.value,
            "raw_score":      self.raw_score,
            "weighted_score": self.weighted_score,
            "strengths":      [s.to_dict() for s in self.strengths],
            "gaps":           [g.to_dict() for g in self.gaps],
            "narrative":      self.narrative,
        }


# ---------------------------------------------------------------------------
# MatchExplanation
# ---------------------------------------------------------------------------

@dataclass
class MatchExplanation:
    """
    The complete explainability output for a Candidate ↔ Drive match.

    Embedded inside a MatchResult. Powers:
        - Recruiter views: "Why is this candidate recommended?"
        - Candidate views: "Why am I ranked here? What can I improve?"
        - Admin dashboards: Dimension-by-dimension match analysis

    Design Invariant:
        Every strength and gap in this explanation must reference a valid
        MatchDimension and must carry a non-empty description. The Phase 5.2
        scoring engines are responsible for populating these with verbatim
        evidence from the intelligence profiles.

    Attributes:
        strengths:           All positive alignments across all dimensions.
        gaps:                All missing or weak capabilities across all dimensions.
        dimension_breakdown: Per-dimension score + narrative. One entry per
                             scored dimension.
        overall_narrative:   One-paragraph executive summary of the match.
                             Derived deterministically from scores and top
                             strengths/gaps — never from an LLM call.
    """
    strengths:           List[MatchStrength]      = field(default_factory=list)
    gaps:                List[MatchGap]            = field(default_factory=list)
    dimension_breakdown: List[DimensionBreakdown]  = field(default_factory=list)
    overall_narrative:   str                       = ""

    def __post_init__(self) -> None:
        """Validate list element types."""
        if not isinstance(self.strengths, list):
            raise TypeError("strengths must be a list.")
        for i, s in enumerate(self.strengths):
            if not isinstance(s, MatchStrength):
                raise TypeError(
                    f"strengths[{i}] must be a MatchStrength instance, "
                    f"got {type(s).__name__!r}."
                )

        if not isinstance(self.gaps, list):
            raise TypeError("gaps must be a list.")
        for i, g in enumerate(self.gaps):
            if not isinstance(g, MatchGap):
                raise TypeError(
                    f"gaps[{i}] must be a MatchGap instance, "
                    f"got {type(g).__name__!r}."
                )

        if not isinstance(self.dimension_breakdown, list):
            raise TypeError("dimension_breakdown must be a list.")
        for i, db in enumerate(self.dimension_breakdown):
            if not isinstance(db, DimensionBreakdown):
                raise TypeError(
                    f"dimension_breakdown[{i}] must be a DimensionBreakdown instance, "
                    f"got {type(db).__name__!r}."
                )

        if not isinstance(self.overall_narrative, str):
            raise TypeError("overall_narrative must be a str.")

    @property
    def critical_gap_count(self) -> int:
        """Number of gaps with GapSeverity.CRITICAL."""
        return sum(1 for g in self.gaps if g.severity == GapSeverity.CRITICAL)

    @property
    def high_gap_count(self) -> int:
        """Number of gaps with GapSeverity.HIGH."""
        return sum(1 for g in self.gaps if g.severity == GapSeverity.HIGH)

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON-safe API serialization."""
        return {
            "strengths":           [s.to_dict() for s in self.strengths],
            "gaps":                [g.to_dict() for g in self.gaps],
            "dimension_breakdown": [db.to_dict() for db in self.dimension_breakdown],
            "overall_narrative":   self.overall_narrative,
            "critical_gap_count":  self.critical_gap_count,
            "high_gap_count":      self.high_gap_count,
        }
