"""
app/matching/models/result.py
------------------------------
Match Result model for Phase 5 — Matching Intelligence.

Design Rules:
    - Pure standard library dataclasses only.
    - Zero framework dependencies.
    - Fully serializable via dataclasses.asdict() and to_dict().
    - MatchResult is the primary output object of the Phase 5 Matching Engine.
    - MatchTier is derived deterministically from the overall_score — never
      set by the caller or an LLM.
    - candidate_id and drive_id are UUIDs validated as strings. They correspond
      to the PKs of the Student/ResumeFile and PlacementDrive entities.

Phase 5.1 — Foundation Only. No scoring logic is implemented here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.matching.enums import MatchTier
from app.matching.models.explanation import MatchExplanation
from app.matching.models.scores import MatchScore


# ---------------------------------------------------------------------------
# Validation helpers (local, not exported)
# ---------------------------------------------------------------------------

def _validate_uuid_str(value: str, field_name: str) -> str:
    """
    Validate that a string is a valid UUID (any version).

    Args:
        value:      The string to validate.
        field_name: Name of the field for error messages.

    Returns:
        The original string if valid.

    Raises:
        TypeError:  If value is not a str.
        ValueError: If value is not a valid UUID string.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a str (UUID), got {type(value).__name__!r}."
        )
    try:
        uuid.UUID(value)
    except ValueError:
        raise ValueError(
            f"{field_name} must be a valid UUID string, got {value!r}."
        )
    return value


# ---------------------------------------------------------------------------
# MatchResult
# ---------------------------------------------------------------------------

@dataclass
class MatchResult:
    """
    Primary output of the Phase 5 Matching Engine.

    Represents the complete result of scoring one candidate against one drive.
    Contains the numeric score, the tier label, and the full explainability
    output. Designed for direct API serialization and future JSONB persistence.

    Design Invariants:
        - candidate_id and drive_id must be valid UUID strings.
        - match_tier is always derived from score.overall_score via
          MatchTier.from_score(). It is set automatically at construction.
        - generated_at is always UTC and set automatically.
        - matching_weights_version records which weight configuration was used,
          enabling future reproducibility and A/B testing.

    Persistence Note (Phase 5.3):
        MatchResult will be serialized as JSONB in a match_results table,
        following the pattern of CandidateIntelligenceSnapshotModel and
        DriveSnapshotModel.

    Attributes:
        candidate_id:             UUID string of the candidate's ResumeFile.
        drive_id:                 UUID string of the PlacementDrive.
        score:                    The complete MatchScore with dimension breakdown.
        explanation:              Explainability output (strengths, gaps, breakdown).
        match_tier:               Derived label (WEAK … EXCELLENT). Set automatically.
        matching_weights_version: Version of MatchingWeights config used.
                                  Enables reproducibility.
        generated_at:             UTC timestamp of result generation.
    """
    candidate_id:             str
    drive_id:                 str
    score:                    MatchScore
    explanation:              MatchExplanation
    matching_weights_version: str          = "default_v1"
    match_tier:               MatchTier    = field(init=False)
    generated_at:             datetime     = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """Validate IDs, score, explanation, and derive match_tier."""
        self.candidate_id = _validate_uuid_str(self.candidate_id, "candidate_id")
        self.drive_id     = _validate_uuid_str(self.drive_id,     "drive_id")

        if not isinstance(self.score, MatchScore):
            raise TypeError(
                f"score must be a MatchScore instance, got {type(self.score).__name__!r}."
            )
        if not isinstance(self.explanation, MatchExplanation):
            raise TypeError(
                f"explanation must be a MatchExplanation instance, "
                f"got {type(self.explanation).__name__!r}."
            )
        if not isinstance(self.matching_weights_version, str) or \
                not self.matching_weights_version.strip():
            raise ValueError("matching_weights_version must be a non-empty string.")

        # Derive tier deterministically from overall score
        self.match_tier = MatchTier.from_score(self.score.overall_score)

    def to_dict(self) -> dict:
        """
        Serialize to a plain dict suitable for JSONB storage and API responses.

        Mirrors the to_dict() pattern used by CandidateIntelligenceProfile,
        ReadinessAnalysisResult, and DriveIntelligenceProfile.
        """
        return {
            "candidate_id":             self.candidate_id,
            "drive_id":                 self.drive_id,
            "match_tier":               self.match_tier.value,
            "score":                    self.score.to_dict(),
            "explanation":              self.explanation.to_dict(),
            "matching_weights_version": self.matching_weights_version,
            "generated_at":             self.generated_at.isoformat(),
        }
