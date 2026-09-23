"""
app/matching
------------
SkillFit Phase 5 — Matching Intelligence Domain.

This package contains the Matching Engine contracts, models, and engine
implementations for the SkillFit Candidate ↔ Drive matching pipeline.

Phase Roadmap:
    Phase 5.1 — Matching Foundation (this package):
                 Domain contracts, score models, explanation models, engine
                 protocols, and weight configuration. No business logic.
    Phase 5.2 — Dimension Scoring:
                 Technology, competency, domain, and signal scoring algorithms.
    Phase 5.3 — Ranking and Recommendations:
                 Candidate ranking per drive, drive ranking per candidate,
                 recommendation API endpoints.

Design Rules (enforced across all sub-modules):
    - Pure standard library dataclasses for all domain models.
    - Zero framework dependencies (no SQLAlchemy, FastAPI, Pydantic, or LLM clients).
    - All models fully serializable via dataclasses.asdict().
    - Enums imported exclusively from app.core.enums — never redefined here.
    - No business logic in Phase 5.1. Foundation only.

Consumed by:
    Phase 5.2:  Dimension scoring engines
    Phase 5.3:  Ranking engine and recommendation services
    APIs:       Recruiter recommendation endpoints, candidate drive feed
"""

from app.matching.models.scores import (
    DimensionScore,
    MatchScore,
)
from app.matching.models.explanation import (
    MatchStrength,
    MatchGap,
    MatchExplanation,
    DimensionBreakdown,
)
from app.matching.models.result import MatchResult
from app.matching.models.weights import MatchingWeights
from app.matching.models.context import MatchingContext, MatchingRequest
from app.matching.enums import (
    MatchDimension,
    MatchTier,
    GapSeverity,
)

__all__ = [
    # Score models
    "DimensionScore",
    "MatchScore",
    # Explanation models
    "MatchStrength",
    "MatchGap",
    "MatchExplanation",
    "DimensionBreakdown",
    # Result model
    "MatchResult",
    # Configuration models
    "MatchingWeights",
    # Context models
    "MatchingContext",
    "MatchingRequest",
    # Enums
    "MatchDimension",
    "MatchTier",
    "GapSeverity",
]
