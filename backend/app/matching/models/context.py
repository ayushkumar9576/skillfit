"""
app/matching/models/context.py
-------------------------------
Context and request models for Phase 5 — Matching Intelligence.

Design Rules:
    - Pure standard library dataclasses only.
    - Zero framework dependencies.
    - MatchingContext packages all inputs to the Matching Engine into a single
      validated container, preventing partial initialization and enforcing that
      the engine always has everything it needs.
    - MatchingRequest is a lightweight request descriptor used by Phase 5.3
      to enqueue and trace matching jobs.

Rationale for MatchingContext:
    The Phase 5.2 scoring engines need four things to produce a MatchResult:
        1. The CandidateIntelligenceProfile (what the candidate knows)
        2. The DriveIntelligenceProfile (what the drive requires)
        3. MatchingWeights (how to weight the six dimensions)
        4. Identifiers (candidate_id, drive_id) for the output MatchResult

    Rather than passing these as four separate arguments through every scoring
    function, MatchingContext bundles them into a validated struct. This also
    makes the engine interface (Phase 5.1 protocols) clean and future-safe.

Phase 5.1 — Foundation Only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

from app.analysis.models.candidate_profile import CandidateIntelligenceProfile
from app.matching.models.weights import MatchingWeights

# Drive intelligence profile is imported lazily below to avoid a circular
# import path. Phase 4 DriveIntelligenceProfile lives in:
#   app.analysis.drives.schemas.intelligence.DriveIntelligenceProfile (Pydantic)
# We use TYPE_CHECKING to keep the type annotation without a hard runtime import.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.analysis.drives.schemas.intelligence import DriveIntelligenceProfile


# ---------------------------------------------------------------------------
# Validation helpers (local, not exported)
# ---------------------------------------------------------------------------

def _validate_uuid_str(value: str, field_name: str) -> str:
    """Validate that a string is a valid UUID."""
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
# MatchingContext
# ---------------------------------------------------------------------------

@dataclass
class MatchingContext:
    """
    Validated input container for the Phase 5 Matching Engine.

    Bundles all data required to produce a MatchResult in a single,
    validated struct. The Matching Engine (Phase 5.2) receives a
    MatchingContext and returns a MatchResult.

    Design Invariants:
        - candidate_profile and drive_profile must be provided (not None).
        - candidate_id and drive_id must be valid UUID strings.
        - weights defaults to MatchingWeights.default() if not supplied.
        - The context is immutable after construction — the scoring engine
          must not mutate it.

    Attributes:
        candidate_id:      UUID string of the candidate's ResumeFile.
        drive_id:          UUID string of the PlacementDrive.
        candidate_profile: The full CandidateIntelligenceProfile.
        drive_profile:     The full DriveIntelligenceProfile (Pydantic model).
        weights:           Weight configuration for this match run.
                           Defaults to MatchingWeights.default().
    """
    candidate_id:      str
    drive_id:          str
    candidate_profile: CandidateIntelligenceProfile
    drive_profile:     "DriveIntelligenceProfile"
    weights:           MatchingWeights = field(
        default_factory=MatchingWeights.default
    )

    def __post_init__(self) -> None:
        """Validate all fields."""
        self.candidate_id = _validate_uuid_str(self.candidate_id, "candidate_id")
        self.drive_id     = _validate_uuid_str(self.drive_id,     "drive_id")

        if not isinstance(self.candidate_profile, CandidateIntelligenceProfile):
            raise TypeError(
                f"candidate_profile must be a CandidateIntelligenceProfile instance, "
                f"got {type(self.candidate_profile).__name__!r}."
            )

        if self.candidate_profile is None:
            raise ValueError("candidate_profile must not be None.")

        if self.drive_profile is None:
            raise ValueError("drive_profile must not be None.")

        if not isinstance(self.weights, MatchingWeights):
            raise TypeError(
                f"weights must be a MatchingWeights instance, "
                f"got {type(self.weights).__name__!r}."
            )


# ---------------------------------------------------------------------------
# MatchingRequest
# ---------------------------------------------------------------------------

@dataclass
class MatchingRequest:
    """
    Lightweight descriptor for a matching job.

    Used by Phase 5.3 services to enqueue, trace, and log matching runs
    without passing the full profile objects through service boundaries.
    The actual matching work is done after the service hydrates the full
    MatchingContext from these IDs.

    Attributes:
        candidate_id:             UUID string of the candidate's ResumeFile.
        drive_id:                 UUID string of the PlacementDrive.
        weights_version:          Which weight configuration to use.
                                  Defaults to "default_v1".
        requested_by:             Who/what triggered this matching run.
                                  Examples: "admin_bulk_match",
                                            "student_browse",
                                            "scheduled_refresh".
    """
    candidate_id:    str
    drive_id:        str
    weights_version: str = "default_v1"
    requested_by:    str = "system"

    def __post_init__(self) -> None:
        """Validate UUIDs and non-empty strings."""
        self.candidate_id = _validate_uuid_str(self.candidate_id, "candidate_id")
        self.drive_id     = _validate_uuid_str(self.drive_id,     "drive_id")

        if not isinstance(self.weights_version, str) or \
                not self.weights_version.strip():
            raise ValueError("weights_version must be a non-empty string.")

        if not isinstance(self.requested_by, str) or \
                not self.requested_by.strip():
            raise ValueError("requested_by must be a non-empty string.")

    def to_dict(self) -> dict:
        """Serialize to a plain dict for logging and API tracing."""
        return {
            "candidate_id":    self.candidate_id,
            "drive_id":        self.drive_id,
            "weights_version": self.weights_version,
            "requested_by":    self.requested_by,
        }
