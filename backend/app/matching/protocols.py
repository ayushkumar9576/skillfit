"""
app/matching/protocols.py
--------------------------
Engine interface contracts (Protocols) for Phase 5 — Matching Intelligence.

Design Rules:
    - Uses typing.Protocol for structural subtyping — no base classes.
    - Zero implementation. Protocols define contracts only.
    - All Protocol methods are documented with their Phase 5.2 and Phase 5.3
      implementation obligations.
    - Following the project's existing patterns: no ABC, no dependency injection
      frameworks, no abstract base classes.

Why Protocols instead of ABCs?
    The project uses function-based services and dataclasses, not class
    hierarchies. typing.Protocol is the idiomatic Python approach for defining
    structural contracts without forcing inheritance. It is also mypy-friendly
    and allows the concrete implementations in Phase 5.2 to be testable in
    isolation without inheriting from a base class.

Phase 5.1 — Contracts Only.
"""

from __future__ import annotations

from typing import List, Protocol, runtime_checkable

from app.matching.models.context import MatchingContext, MatchingRequest
from app.matching.models.result import MatchResult
from app.matching.models.scores import DimensionScore, MatchScore
from app.matching.models.weights import MatchingWeights


# ---------------------------------------------------------------------------
# DimensionScorer Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class DimensionScorer(Protocol):
    """
    Contract for a single-dimension scoring engine.

    Phase 5.2 will implement one concrete DimensionScorer per MatchDimension:
        TechnologyScorer   — scores TECHNOLOGY dimension
        CompetencyScorer   — scores COMPETENCY dimension
        DomainScorer       — scores DOMAIN dimension
        SignalScorer       — scores SIGNAL dimension
        ProjectScorer      — scores PROJECT dimension
        BehavioralScorer   — scores BEHAVIORAL dimension

    Each scorer receives the full MatchingContext and returns a DimensionScore
    for its dimension only. This makes scorers independently testable.

    Implementation Requirements (Phase 5.2):
        - Must not raise exceptions for empty dimension data; return a
          DimensionScore with raw_score=0.0 and total_items=0.
        - Must populate reasoning with a human-readable explanation.
        - Must set matched_items and total_items accurately.
        - Must not call the LLM or make any I/O calls.
        - Must be purely deterministic — same inputs always produce same output.
    """

    def score(self, context: MatchingContext) -> DimensionScore:
        """
        Score one dimension for a candidate ↔ drive match.

        Args:
            context: The fully validated MatchingContext containing both
                     intelligence profiles and weight configuration.

        Returns:
            A validated DimensionScore for this scorer's dimension.
        """
        ...


# ---------------------------------------------------------------------------
# MatchingEngine Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class MatchingEngine(Protocol):
    """
    Contract for the core Phase 5 Matching Engine.

    The Matching Engine orchestrates all DimensionScorers and aggregates their
    results into a final MatchResult.

    Phase 5.2 will implement the concrete SkillFitMatchingEngine class.

    Implementation Requirements (Phase 5.2):
        - Must invoke all registered DimensionScorers.
        - Must normalize dimension weights before computing overall_score.
        - Must populate MatchExplanation from DimensionScore results.
        - Must derive MatchTier deterministically from the overall_score.
        - Must not call the LLM or make any I/O calls.
        - Must be purely deterministic — same inputs always produce same output.
        - Must handle empty intelligence profiles gracefully (return score=0.0).
    """

    def score_candidate_against_drive(
        self,
        context: MatchingContext,
    ) -> MatchResult:
        """
        Score a single candidate against a single drive.

        This is the primary entry point for the Matching Engine.

        Args:
            context: The fully validated MatchingContext containing both
                     intelligence profiles and weight configuration.

        Returns:
            A MatchResult with full score, tier, and explanation.

        Raises:
            ValueError: If context is not a valid MatchingContext.
        """
        ...

    def score_drive_against_candidate(
        self,
        context: MatchingContext,
    ) -> MatchResult:
        """
        Score a single drive against a single candidate.

        Semantically equivalent to score_candidate_against_drive — the
        MatchResult is the same. This method exists to support the symmetric
        API endpoints:
            GET /students/{id}/recommended-drives   → uses candidate_against_drive
            GET /drives/{id}/recommended-candidates → uses drive_against_candidate

        Phase 5.3 may delegate both to the same underlying implementation.

        Args:
            context: The fully validated MatchingContext.

        Returns:
            A MatchResult with full score, tier, and explanation.
        """
        ...


# ---------------------------------------------------------------------------
# RankingEngine Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class RankingEngine(Protocol):
    """
    Contract for the Phase 5.3 Ranking Engine.

    The Ranking Engine sorts a list of MatchResults for presentation in
    recommendation endpoints. Phase 5.1 defines the contract only.

    Phase 5.3 Implementation Requirements:
        - Must sort by MatchScore.overall_score descending.
        - Must accept an optional limit parameter.
        - Must not produce side effects (pure function contract).
        - Ties must be broken by match_tier order (EXCELLENT first), then
          by generated_at ascending (earlier matches are more stable).
    """

    def rank_candidates_for_drive(
        self,
        results: List[MatchResult],
        limit: int | None = None,
    ) -> List[MatchResult]:
        """
        Sort and optionally truncate a list of candidate match results
        for a single drive.

        Args:
            results: Unordered list of MatchResults for different candidates
                     against the same drive.
            limit:   Maximum number of results to return. None means all.

        Returns:
            Sorted list of MatchResults, best match first.
        """
        ...

    def rank_drives_for_candidate(
        self,
        results: List[MatchResult],
        limit: int | None = None,
    ) -> List[MatchResult]:
        """
        Sort and optionally truncate a list of drive match results
        for a single candidate.

        Args:
            results: Unordered list of MatchResults for different drives
                     against the same candidate.
            limit:   Maximum number of results to return. None means all.

        Returns:
            Sorted list of MatchResults, best match first.
        """
        ...
