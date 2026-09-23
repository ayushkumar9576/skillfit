"""
app/matching/models/weights.py
-------------------------------
Matching weight configuration for Phase 5 — Matching Intelligence.

Design Rules:
    - Pure standard library dataclasses only.
    - Zero framework dependencies.
    - MatchingWeights is a pure configuration object — it contains no
      scoring logic. It describes *how much* each dimension matters, not *how*
      to compute the dimension score.
    - All weights must be strictly positive (> 0.0).
    - Weights do not need to sum to 1.0 — the scoring engine normalizes them.
    - MatchingWeights is versioned so future drive-specific overrides can be
      tracked and compared (Phase 5.3).

Default Weight Rationale (DEFAULT_WEIGHTS):
    TECHNOLOGY (0.30): Largest single factor. Direct skill alignment is the
                       most reliable signal of role fit.
    COMPETENCY (0.25): Engineering capability patterns (backend, ML, etc.)
                       matter almost as much as raw technologies.
    DOMAIN     (0.15): Domain alignment provides context but can be inferred
                       from competencies, so it carries less independent weight.
    SIGNAL     (0.15): Hiring signals (DSA_FOCUSED, PROJECT_FOCUSED) are
                       important differentiators in campus hiring contexts.
    PROJECT    (0.10): Sophistication indicates readiness but is already
                       partially captured by technologies and competencies.
    BEHAVIORAL (0.05): Behavioral signals are very weakly extracted from
                       resumes; given low precision, they carry low weight.

Phase 5.1 — Foundation Only.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Dict

from app.matching.enums import MatchDimension


# ---------------------------------------------------------------------------
# Default weight configuration
# ---------------------------------------------------------------------------

#: Default weights for the Phase 5 Matching Engine. See module docstring.
DEFAULT_WEIGHTS: Dict[str, float] = {
    MatchDimension.TECHNOLOGY.value: 0.30,
    MatchDimension.COMPETENCY.value: 0.25,
    MatchDimension.DOMAIN.value:     0.15,
    MatchDimension.SIGNAL.value:     0.15,
    MatchDimension.PROJECT.value:    0.10,
    MatchDimension.BEHAVIORAL.value: 0.05,
}

#: Minimum allowed weight for any dimension.
_WEIGHT_MIN: float = 0.0  # exclusive

#: Maximum allowed weight for any dimension.
_WEIGHT_MAX: float = 1.0  # inclusive


# ---------------------------------------------------------------------------
# MatchingWeights
# ---------------------------------------------------------------------------

@dataclass
class MatchingWeights:
    """
    Immutable configuration describing the relative importance of each
    matching dimension.

    The Matching Engine reads these weights to compute weighted_score for each
    DimensionScore, then normalizes them to produce the overall_score in
    MatchScore.

    Immutability:
        MatchingWeights is declared frozen=True. Once constructed, weights
        cannot be mutated. Drive-level overrides must produce a new instance
        via MatchingWeights.with_overrides().

    Drive-level Overrides (Phase 5.3):
        A recruiter or admin may override specific dimension weights for a
        particular drive. For example, a DSA-heavy drive might increase the
        SIGNAL weight and reduce the PROJECT weight. This is achieved by
        calling MatchingWeights.with_overrides() rather than constructing
        a new instance from scratch.

    Validation:
        - All weights must be > 0.0 and <= 1.0.
        - The weights dict must contain an entry for every MatchDimension.
        - No dimension may be omitted — use a very small weight (e.g., 0.01)
          to de-emphasize rather than remove a dimension.

    Attributes:
        weights:  Mapping from MatchDimension string value to float weight.
        version:  Version string for this weight configuration.
                  Used by MatchResult.matching_weights_version for traceability.
    """
    weights: Dict[str, float]
    version: str = "default_v1"

    # frozen=True via field descriptor; we implement immutability manually
    # to stay compatible with pure stdlib dataclasses (no frozen=True needed
    # as this is a configuration object, not a data record).

    def __post_init__(self) -> None:
        """
        Validate that all dimensions are covered and all weights are valid.

        Raises:
            TypeError:  If weights is not a dict.
            KeyError:   If any MatchDimension is missing from weights.
            ValueError: If any weight is outside (0.0, 1.0].
        """
        if not isinstance(self.weights, dict):
            raise TypeError(
                f"weights must be a dict, got {type(self.weights).__name__!r}."
            )

        # Every dimension must be present
        required = {d.value for d in MatchDimension}
        provided = set(self.weights.keys())
        missing  = required - provided
        if missing:
            raise KeyError(
                f"MatchingWeights is missing entries for dimensions: {sorted(missing)}. "
                f"All six dimensions must have a weight."
            )

        # Validate each weight value
        for dim_value, w in self.weights.items():
            if not isinstance(w, (int, float)):
                raise TypeError(
                    f"weights[{dim_value!r}] must be numeric, "
                    f"got {type(w).__name__!r}."
                )
            w_f = float(w)
            if w_f != w_f:  # NaN check
                raise ValueError(f"weights[{dim_value!r}] must not be NaN.")
            if w_f <= _WEIGHT_MIN or w_f > _WEIGHT_MAX:
                raise ValueError(
                    f"weights[{dim_value!r}] must be in ({_WEIGHT_MIN}, {_WEIGHT_MAX}], "
                    f"got {w_f!r}."
                )
            self.weights[dim_value] = w_f

        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("version must be a non-empty string.")

    def get_weight(self, dimension: MatchDimension) -> float:
        """
        Retrieve the weight for a specific MatchDimension.

        Args:
            dimension: The MatchDimension to retrieve the weight for.

        Returns:
            The float weight for this dimension.

        Raises:
            TypeError: If dimension is not a MatchDimension.
            KeyError:  If the dimension is somehow not in weights (should not
                       happen after __post_init__ validation).
        """
        if not isinstance(dimension, MatchDimension):
            raise TypeError(
                f"dimension must be a MatchDimension, got {type(dimension).__name__!r}."
            )
        return self.weights[dimension.value]

    def normalized(self) -> Dict[str, float]:
        """
        Return a copy of weights normalized so they sum to 1.0.

        The Matching Engine calls this before applying weights to dimension
        scores, ensuring that a set of weights like {0.3, 0.25, 0.15, 0.15,
        0.10, 0.05} produces the correct weighted average.

        Returns:
            A new dict with the same keys but normalized float values.
        """
        total = sum(self.weights.values())
        return {k: v / total for k, v in self.weights.items()}

    def with_overrides(
        self,
        overrides: Dict[str, float],
        new_version: str = "override_v1",
    ) -> "MatchingWeights":
        """
        Produce a new MatchingWeights with specific dimensions overridden.

        The caller provides only the dimensions they wish to change. All
        other dimensions retain their current weights. The result is a fully
        validated new MatchingWeights instance.

        Args:
            overrides:   Dict of {MatchDimension.value: new_weight} pairs.
            new_version: Version string for the resulting configuration.

        Returns:
            A new MatchingWeights instance with overrides applied.

        Raises:
            ValueError: If any override key is not a valid MatchDimension value.
        """
        valid_values = {d.value for d in MatchDimension}
        for key in overrides:
            if key not in valid_values:
                raise ValueError(
                    f"Override key {key!r} is not a valid MatchDimension value. "
                    f"Valid values: {sorted(valid_values)}."
                )

        merged = {**self.weights, **overrides}
        return MatchingWeights(weights=merged, version=new_version)

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON-safe storage."""
        return {
            "weights": dict(self.weights),
            "version": self.version,
        }

    @classmethod
    def default(cls) -> "MatchingWeights":
        """
        Construct the default MatchingWeights using DEFAULT_WEIGHTS.

        Returns:
            A fully validated MatchingWeights with the default configuration.
        """
        return cls(weights=dict(DEFAULT_WEIGHTS), version="default_v1")
