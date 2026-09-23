"""
app/matching/models/__init__.py
--------------------------------
Re-exports for all Phase 5.1 Matching domain models.
"""

from app.matching.models.scores import DimensionScore, MatchScore
from app.matching.models.explanation import (
    MatchStrength,
    MatchGap,
    MatchExplanation,
    DimensionBreakdown,
)
from app.matching.models.result import MatchResult
from app.matching.models.weights import MatchingWeights
from app.matching.models.context import MatchingContext, MatchingRequest

__all__ = [
    "DimensionScore",
    "MatchScore",
    "MatchStrength",
    "MatchGap",
    "MatchExplanation",
    "DimensionBreakdown",
    "MatchResult",
    "MatchingWeights",
    "MatchingContext",
    "MatchingRequest",
]
