"""
app/matching/models/scores.py
------------------------------
Score models for Phase 5 — Matching Intelligence.

Design Rules:
    - Pure standard library dataclasses only.
    - Zero framework dependencies.
    - Fully serializable via dataclasses.asdict().
    - All scores are normalized to [0.0, 1.0] for consistent comparison.
    - Validation is strict: invalid states raise ValueError at construction.

Score Architecture:
    DimensionScore    — result of scoring one dimension (e.g., TECHNOLOGY)
    MatchScore        — aggregate of all DimensionScores into an overall result

Phase 5.1 — Foundation Only. No scoring logic is implemented here.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Dict, List

from app.matching.enums import MatchDimension


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: All normalized scores must fall within [SCORE_MIN, SCORE_MAX].
SCORE_MIN: float = 0.0
SCORE_MAX: float = 1.0

#: All weights must be strictly positive.
WEIGHT_MIN: float = 0.0  # exclusive


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_score(value: float, field_name: str) -> float:
    """
    Validate that a score is a finite float within [SCORE_MIN, SCORE_MAX].

    Args:
        value:      The score value to validate.
        field_name: Name of the field, used in error messages.

    Returns:
        The validated value.

    Raises:
        TypeError:  If value is not a float or int.
        ValueError: If value is outside [0.0, 1.0] or is NaN/Inf.
    """
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"{field_name} must be a numeric value, got {type(value).__name__!r}."
        )
    value = float(value)
    if value != value:  # NaN check
        raise ValueError(f"{field_name} must not be NaN.")
    if value < SCORE_MIN or value > SCORE_MAX:
        raise ValueError(
            f"{field_name} must be in [{SCORE_MIN}, {SCORE_MAX}], got {value!r}."
        )
    return value


def _validate_weight(value: float, field_name: str) -> float:
    """
    Validate that a weight is a strictly positive finite float.

    Args:
        value:      The weight value to validate.
        field_name: Name of the field, used in error messages.

    Returns:
        The validated value.

    Raises:
        TypeError:  If value is not a float or int.
        ValueError: If value is not > 0 or is NaN/Inf.
    """
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"{field_name} must be a numeric value, got {type(value).__name__!r}."
        )
    value = float(value)
    if value != value:
        raise ValueError(f"{field_name} must not be NaN.")
    if value <= WEIGHT_MIN:
        raise ValueError(
            f"{field_name} must be > {WEIGHT_MIN}, got {value!r}."
        )
    return value


# ---------------------------------------------------------------------------
# DimensionScore
# ---------------------------------------------------------------------------

@dataclass
class DimensionScore:
    """
    Score result for a single matching dimension (e.g., TECHNOLOGY or COMPETENCY).

    Produced by a dimension-specific scoring engine in Phase 5.2 and aggregated
    into a MatchScore by the Matching Engine in Phase 5.3.

    Design Invariants:
        - raw_score and weighted_score are in [0.0, 1.0].
        - weight must be strictly positive (> 0.0).
        - weighted_score = raw_score * weight / (sum of all weights).
          However, Phase 5.1 does not enforce this relationship — the scoring
          engine in Phase 5.2 is responsible for computing it correctly.
        - matched_items and total_items describe coverage:
              matched_items ≤ total_items
              total_items = 0 means no drive requirements in this dimension.

    Attributes:
        dimension:      The matching dimension this score covers.
        raw_score:      Unweighted normalized score in [0.0, 1.0].
        weight:         Importance multiplier (> 0.0). Default 1.0.
        weighted_score: raw_score × normalized weight. In [0.0, 1.0].
        matched_items:  Count of requirements met by the candidate.
        total_items:    Total requirements in this dimension from the drive.
        reasoning:      Short human-readable explanation of how this score
                        was computed. Used by the explainability layer.
    """
    dimension:      MatchDimension
    raw_score:      float
    weight:         float
    weighted_score: float
    matched_items:  int = 0
    total_items:    int = 0
    reasoning:      str = ""

    def __post_init__(self) -> None:
        """Validate all numeric fields after dataclass initialization."""
        self.raw_score      = _validate_score(self.raw_score, "raw_score")
        self.weighted_score = _validate_score(self.weighted_score, "weighted_score")
        self.weight         = _validate_weight(self.weight, "weight")

        if not isinstance(self.matched_items, int) or self.matched_items < 0:
            raise ValueError(
                f"matched_items must be a non-negative int, got {self.matched_items!r}."
            )
        if not isinstance(self.total_items, int) or self.total_items < 0:
            raise ValueError(
                f"total_items must be a non-negative int, got {self.total_items!r}."
            )
        if self.matched_items > self.total_items:
            raise ValueError(
                f"matched_items ({self.matched_items}) cannot exceed "
                f"total_items ({self.total_items})."
            )
        if not isinstance(self.dimension, MatchDimension):
            raise TypeError(
                f"dimension must be a MatchDimension instance, got {type(self.dimension).__name__!r}."
            )

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON-safe storage and API serialization."""
        return {
            "dimension":      self.dimension.value,
            "raw_score":      self.raw_score,
            "weight":         self.weight,
            "weighted_score": self.weighted_score,
            "matched_items":  self.matched_items,
            "total_items":    self.total_items,
            "reasoning":      self.reasoning,
        }


# ---------------------------------------------------------------------------
# MatchScore
# ---------------------------------------------------------------------------

@dataclass
class MatchScore:
    """
    The complete aggregated score for a Candidate ↔ Drive match.

    MatchScore is the primary numeric output of the Phase 5 Matching Engine.
    It is embedded inside a MatchResult for persistence and API serialization.

    Score Architecture:
        Each of the six dimension scores is computed independently by a
        dimension scorer (Phase 5.2). This class aggregates them into a
        single overall_score and provides a structured view by dimension.

    Invariants:
        - overall_score and all dimension scores are in [0.0, 1.0].
        - dimension_scores is keyed by MatchDimension values.
        - overall_score must equal the weighted average of dimension_scores.
          Phase 5.1 does not enforce this at model level — the scorer owns it.
        - An empty dimension_scores dict is valid (represents a drive with no
          extractable requirements), resulting in overall_score = 0.0.

    Attributes:
        overall_score:     Weighted-average across all active dimensions.
                           Normalized to [0.0, 1.0].
        dimension_scores:  Per-dimension score breakdown.
                           Keyed by MatchDimension enum value (string).
        coverage_ratio:    Fraction of drive dimensions with at least one
                           requirement (total_items > 0). Indicates how
                           much of the drive was matchable.
        scoring_version:   Version string of the scoring algorithm that
                           produced this score. Used for reproducibility
                           and future A/B testing.
    """
    overall_score:    float
    dimension_scores: Dict[str, DimensionScore] = field(default_factory=dict)
    coverage_ratio:   float = 1.0
    scoring_version:  str   = "5.2.0"

    def __post_init__(self) -> None:
        """Validate all numeric fields and dimension_scores structure."""
        self.overall_score  = _validate_score(self.overall_score, "overall_score")
        self.coverage_ratio = _validate_score(self.coverage_ratio, "coverage_ratio")

        if not isinstance(self.dimension_scores, dict):
            raise TypeError(
                f"dimension_scores must be a dict, got {type(self.dimension_scores).__name__!r}."
            )

        for key, val in self.dimension_scores.items():
            if not isinstance(key, str):
                raise TypeError(
                    f"dimension_scores keys must be strings, got {type(key).__name__!r}."
                )
            if not isinstance(val, DimensionScore):
                raise TypeError(
                    f"dimension_scores[{key!r}] must be a DimensionScore instance, "
                    f"got {type(val).__name__!r}."
                )

    def get_dimension(self, dimension: MatchDimension) -> DimensionScore | None:
        """
        Retrieve the DimensionScore for a given dimension.

        Args:
            dimension: The MatchDimension to retrieve.

        Returns:
            DimensionScore if the dimension was scored, else None.
        """
        return self.dimension_scores.get(dimension.value)

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON-safe storage and API serialization."""
        return {
            "overall_score":    self.overall_score,
            "dimension_scores": {k: v.to_dict() for k, v in self.dimension_scores.items()},
            "coverage_ratio":   self.coverage_ratio,
            "scoring_version":  self.scoring_version,
        }

    @classmethod
    def zero(cls, scoring_version: str = "5.2.0") -> "MatchScore":
        """
        Construct a zero-value MatchScore for cases where scoring is
        not possible (e.g., empty drive, missing intelligence).

        Args:
            scoring_version: Version string of the scoring engine.

        Returns:
            MatchScore with overall_score=0.0 and no dimension scores.
        """
        return cls(
            overall_score=0.0,
            dimension_scores={},
            coverage_ratio=0.0,
            scoring_version=scoring_version,
        )
