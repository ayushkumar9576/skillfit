"""
scripts/test_phase5_matching_foundation.py
-------------------------------------------
Comprehensive test suite for Phase 5.1 — Matching Foundation.

Tests all models, enums, validation rules, boundary conditions,
and serialization behavior.

Run:
    python -m pytest scripts/test_phase5_matching_foundation.py -v
    -- or --
    python scripts/test_phase5_matching_foundation.py

Coverage:
    - MatchDimension, MatchTier, GapSeverity enums
    - MatchTier.from_score() boundary conditions
    - DimensionScore construction and validation
    - MatchScore construction, get_dimension(), MatchScore.zero()
    - MatchStrength construction and validation
    - MatchGap construction and validation
    - DimensionBreakdown construction and validation
    - MatchExplanation construction, critical_gap_count, high_gap_count
    - MatchResult construction, match_tier derivation, to_dict()
    - MatchingWeights construction, normalized(), with_overrides(), default()
    - MatchingRequest construction and validation
    - All to_dict() serialization outputs
    - Protocol structural checks (DimensionScorer, MatchingEngine, RankingEngine)
"""

import json
import sys
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, List

# Ensure backend app is importable
sys.path.insert(0, ".")

# ---------------------------------------------------------------------------
# Test Infrastructure
# ---------------------------------------------------------------------------

_pass_count = 0
_fail_count = 0
_skip_count = 0


def _run(name: str, fn) -> None:
    """Run a single test function and record pass/fail."""
    global _pass_count, _fail_count
    try:
        fn()
        _pass_count += 1
        print(f"  PASS  {name}")
    except AssertionError as exc:
        _fail_count += 1
        print(f"  FAIL  {name}")
        print(f"        AssertionError: {exc}")
    except Exception as exc:
        _fail_count += 1
        print(f"  FAIL  {name}")
        traceback.print_exc()


def _expect_raises(exc_type, fn, msg_fragment: str = "") -> None:
    """Assert that fn() raises exc_type, optionally checking the message."""
    try:
        fn()
        raise AssertionError(
            f"Expected {exc_type.__name__} but no exception was raised."
        )
    except exc_type as exc:
        if msg_fragment and msg_fragment not in str(exc):
            raise AssertionError(
                f"Expected message to contain {msg_fragment!r}, got: {exc!r}"
            )


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from app.matching.enums import GapSeverity, MatchDimension, MatchTier
from app.matching.models.scores import DimensionScore, MatchScore
from app.matching.models.explanation import (
    DimensionBreakdown,
    MatchExplanation,
    MatchGap,
    MatchStrength,
)
from app.matching.models.result import MatchResult
from app.matching.models.weights import MatchingWeights
from app.matching.models.context import MatchingRequest
from app.matching.protocols import DimensionScorer, MatchingEngine, RankingEngine


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

_CAND_ID  = str(uuid.uuid4())
_DRIVE_ID = str(uuid.uuid4())


def _make_dim_score(
    dimension=MatchDimension.TECHNOLOGY,
    raw_score=0.8,
    weight=0.3,
    weighted_score=0.24,
    matched=4,
    total=5,
) -> DimensionScore:
    return DimensionScore(
        dimension=dimension,
        raw_score=raw_score,
        weight=weight,
        weighted_score=weighted_score,
        matched_items=matched,
        total_items=total,
        reasoning="Test fixture",
    )


def _make_match_score(overall=0.75) -> MatchScore:
    ds = _make_dim_score()
    return MatchScore(
        overall_score=overall,
        dimension_scores={MatchDimension.TECHNOLOGY.value: ds},
    )


def _make_strength() -> MatchStrength:
    return MatchStrength(
        title="Strong Backend",
        dimension=MatchDimension.COMPETENCY,
        description="Candidate has ARCHITECTED-level Django evidence.",
        candidate_evidence="Built Django REST API for e-commerce platform",
        drive_evidence="Must have backend development experience",
        impact_score=0.25,
    )


def _make_gap(severity=GapSeverity.HIGH) -> MatchGap:
    return MatchGap(
        title="Missing: System Design",
        dimension=MatchDimension.COMPETENCY,
        severity=severity,
        description="Drive requires system design skills; candidate lacks evidence.",
        drive_evidence="Candidates must demonstrate system design ability",
        improvement_hint="Practice system design with distributed systems projects.",
    )


def _make_explanation() -> MatchExplanation:
    return MatchExplanation(
        strengths=[_make_strength()],
        gaps=[_make_gap(GapSeverity.CRITICAL), _make_gap(GapSeverity.HIGH)],
        dimension_breakdown=[
            DimensionBreakdown(
                dimension=MatchDimension.TECHNOLOGY,
                raw_score=0.8,
                weighted_score=0.24,
                strengths=[_make_strength()],
                gaps=[_make_gap()],
                narrative="Strong tech match.",
            )
        ],
        overall_narrative="Good match with one critical gap.",
    )


def _make_result() -> MatchResult:
    return MatchResult(
        candidate_id=_CAND_ID,
        drive_id=_DRIVE_ID,
        score=_make_match_score(0.75),
        explanation=_make_explanation(),
    )


# ---------------------------------------------------------------------------
# 1. Enum Tests
# ---------------------------------------------------------------------------

print("\n=== 1. Enum Tests ===")


def test_match_dimension_values():
    assert MatchDimension.TECHNOLOGY.value == "TECHNOLOGY"
    assert MatchDimension.COMPETENCY.value == "COMPETENCY"
    assert MatchDimension.DOMAIN.value == "DOMAIN"
    assert MatchDimension.SIGNAL.value == "SIGNAL"
    assert MatchDimension.PROJECT.value == "PROJECT"
    assert MatchDimension.BEHAVIORAL.value == "BEHAVIORAL"
    assert len(list(MatchDimension)) == 6


def test_match_tier_values():
    assert MatchTier.WEAK.value == "WEAK"
    assert MatchTier.EXCELLENT.value == "EXCELLENT"


def test_gap_severity_values():
    assert GapSeverity.CRITICAL.value == "CRITICAL"
    assert GapSeverity.LOW.value == "LOW"


def test_match_tier_from_score_boundaries():
    assert MatchTier.from_score(0.0)   == MatchTier.WEAK
    assert MatchTier.from_score(0.39)  == MatchTier.WEAK
    assert MatchTier.from_score(0.40)  == MatchTier.PARTIAL
    assert MatchTier.from_score(0.54)  == MatchTier.PARTIAL
    assert MatchTier.from_score(0.55)  == MatchTier.MODERATE
    assert MatchTier.from_score(0.69)  == MatchTier.MODERATE
    assert MatchTier.from_score(0.70)  == MatchTier.STRONG
    assert MatchTier.from_score(0.84)  == MatchTier.STRONG
    assert MatchTier.from_score(0.85)  == MatchTier.EXCELLENT
    assert MatchTier.from_score(1.0)   == MatchTier.EXCELLENT


def test_match_tier_from_score_invalid():
    _expect_raises(ValueError, lambda: MatchTier.from_score(-0.01))
    _expect_raises(ValueError, lambda: MatchTier.from_score(1.01))


for fn in [
    test_match_dimension_values,
    test_match_tier_values,
    test_gap_severity_values,
    test_match_tier_from_score_boundaries,
    test_match_tier_from_score_invalid,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 2. DimensionScore Tests
# ---------------------------------------------------------------------------

print("\n=== 2. DimensionScore Tests ===")


def test_dimension_score_valid_creation():
    ds = _make_dim_score()
    assert ds.dimension == MatchDimension.TECHNOLOGY
    assert ds.raw_score == 0.8
    assert ds.weight == 0.3
    assert ds.weighted_score == 0.24
    assert ds.matched_items == 4
    assert ds.total_items == 5


def test_dimension_score_zero_values_valid():
    ds = DimensionScore(
        dimension=MatchDimension.DOMAIN,
        raw_score=0.0,
        weight=0.01,
        weighted_score=0.0,
        matched_items=0,
        total_items=0,
    )
    assert ds.raw_score == 0.0


def test_dimension_score_boundary_max():
    ds = DimensionScore(
        dimension=MatchDimension.SIGNAL,
        raw_score=1.0,
        weight=1.0,
        weighted_score=1.0,
        matched_items=10,
        total_items=10,
    )
    assert ds.raw_score == 1.0


def test_dimension_score_negative_score_rejected():
    _expect_raises(ValueError, lambda: DimensionScore(
        dimension=MatchDimension.TECHNOLOGY,
        raw_score=-0.01,
        weight=0.3,
        weighted_score=0.0,
        matched_items=0,
        total_items=5,
    ))


def test_dimension_score_score_above_1_rejected():
    _expect_raises(ValueError, lambda: DimensionScore(
        dimension=MatchDimension.TECHNOLOGY,
        raw_score=1.01,
        weight=0.3,
        weighted_score=0.0,
        matched_items=0,
        total_items=5,
    ))


def test_dimension_score_zero_weight_rejected():
    _expect_raises(ValueError, lambda: DimensionScore(
        dimension=MatchDimension.TECHNOLOGY,
        raw_score=0.5,
        weight=0.0,
        weighted_score=0.5,
        matched_items=0,
        total_items=5,
    ))


def test_dimension_score_negative_weight_rejected():
    _expect_raises(ValueError, lambda: DimensionScore(
        dimension=MatchDimension.TECHNOLOGY,
        raw_score=0.5,
        weight=-0.1,
        weighted_score=0.5,
        matched_items=0,
        total_items=5,
    ))


def test_dimension_score_matched_exceeds_total_rejected():
    _expect_raises(ValueError, lambda: DimensionScore(
        dimension=MatchDimension.TECHNOLOGY,
        raw_score=0.5,
        weight=0.3,
        weighted_score=0.15,
        matched_items=6,
        total_items=5,
    ))


def test_dimension_score_invalid_dimension_type_rejected():
    _expect_raises(TypeError, lambda: DimensionScore(
        dimension="TECHNOLOGY",  # string instead of enum
        raw_score=0.5,
        weight=0.3,
        weighted_score=0.15,
        matched_items=0,
        total_items=5,
    ))


def test_dimension_score_to_dict():
    ds = _make_dim_score()
    d  = ds.to_dict()
    assert d["dimension"] == "TECHNOLOGY"
    assert d["raw_score"] == 0.8
    assert d["weight"] == 0.3
    assert d["weighted_score"] == 0.24
    assert d["matched_items"] == 4
    assert d["total_items"] == 5
    # Must be JSON-serializable
    json.dumps(d)


for fn in [
    test_dimension_score_valid_creation,
    test_dimension_score_zero_values_valid,
    test_dimension_score_boundary_max,
    test_dimension_score_negative_score_rejected,
    test_dimension_score_score_above_1_rejected,
    test_dimension_score_zero_weight_rejected,
    test_dimension_score_negative_weight_rejected,
    test_dimension_score_matched_exceeds_total_rejected,
    test_dimension_score_invalid_dimension_type_rejected,
    test_dimension_score_to_dict,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 3. MatchScore Tests
# ---------------------------------------------------------------------------

print("\n=== 3. MatchScore Tests ===")


def test_match_score_valid_creation():
    ms = _make_match_score(0.75)
    assert ms.overall_score == 0.75
    assert len(ms.dimension_scores) == 1


def test_match_score_zero_factory():
    ms = MatchScore.zero()
    assert ms.overall_score == 0.0
    assert ms.coverage_ratio == 0.0
    assert ms.dimension_scores == {}


def test_match_score_invalid_overall_rejected():
    _expect_raises(ValueError, lambda: MatchScore(overall_score=1.5))


def test_match_score_get_dimension_found():
    ds = _make_dim_score()
    ms = MatchScore(
        overall_score=0.5,
        dimension_scores={MatchDimension.TECHNOLOGY.value: ds},
    )
    result = ms.get_dimension(MatchDimension.TECHNOLOGY)
    assert result is ds


def test_match_score_get_dimension_not_found():
    ms = _make_match_score()
    assert ms.get_dimension(MatchDimension.COMPETENCY) is None


def test_match_score_invalid_dimension_scores_type_rejected():
    _expect_raises(TypeError, lambda: MatchScore(
        overall_score=0.5,
        dimension_scores=[],  # list instead of dict
    ))


def test_match_score_to_dict_json_serializable():
    ms = _make_match_score()
    d  = ms.to_dict()
    assert "overall_score" in d
    assert "dimension_scores" in d
    json.dumps(d)


for fn in [
    test_match_score_valid_creation,
    test_match_score_zero_factory,
    test_match_score_invalid_overall_rejected,
    test_match_score_get_dimension_found,
    test_match_score_get_dimension_not_found,
    test_match_score_invalid_dimension_scores_type_rejected,
    test_match_score_to_dict_json_serializable,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 4. MatchStrength Tests
# ---------------------------------------------------------------------------

print("\n=== 4. MatchStrength Tests ===")


def test_match_strength_valid_creation():
    s = _make_strength()
    assert s.title == "Strong Backend"
    assert s.dimension == MatchDimension.COMPETENCY
    assert s.impact_score == 0.25


def test_match_strength_empty_title_rejected():
    _expect_raises(ValueError, lambda: MatchStrength(
        title="",
        dimension=MatchDimension.COMPETENCY,
        description="desc",
    ))


def test_match_strength_whitespace_title_rejected():
    _expect_raises(ValueError, lambda: MatchStrength(
        title="   ",
        dimension=MatchDimension.COMPETENCY,
        description="desc",
    ))


def test_match_strength_empty_description_rejected():
    _expect_raises(ValueError, lambda: MatchStrength(
        title="Title",
        dimension=MatchDimension.COMPETENCY,
        description="",
    ))


def test_match_strength_invalid_impact_score_rejected():
    _expect_raises(ValueError, lambda: MatchStrength(
        title="Title",
        dimension=MatchDimension.COMPETENCY,
        description="desc",
        impact_score=1.5,
    ))


def test_match_strength_invalid_dimension_type_rejected():
    _expect_raises(TypeError, lambda: MatchStrength(
        title="Title",
        dimension="COMPETENCY",  # string
        description="desc",
    ))


def test_match_strength_to_dict():
    d = _make_strength().to_dict()
    assert d["dimension"] == "COMPETENCY"
    assert d["title"] == "Strong Backend"
    json.dumps(d)


for fn in [
    test_match_strength_valid_creation,
    test_match_strength_empty_title_rejected,
    test_match_strength_whitespace_title_rejected,
    test_match_strength_empty_description_rejected,
    test_match_strength_invalid_impact_score_rejected,
    test_match_strength_invalid_dimension_type_rejected,
    test_match_strength_to_dict,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 5. MatchGap Tests
# ---------------------------------------------------------------------------

print("\n=== 5. MatchGap Tests ===")


def test_match_gap_valid_creation():
    g = _make_gap()
    assert g.severity == GapSeverity.HIGH
    assert g.dimension == MatchDimension.COMPETENCY


def test_match_gap_empty_title_rejected():
    _expect_raises(ValueError, lambda: MatchGap(
        title="",
        dimension=MatchDimension.COMPETENCY,
        severity=GapSeverity.HIGH,
        description="desc",
    ))


def test_match_gap_invalid_severity_type_rejected():
    _expect_raises(TypeError, lambda: MatchGap(
        title="Gap",
        dimension=MatchDimension.COMPETENCY,
        severity="HIGH",  # string instead of enum
        description="desc",
    ))


def test_match_gap_to_dict():
    d = _make_gap().to_dict()
    assert d["severity"] == "HIGH"
    json.dumps(d)


for fn in [
    test_match_gap_valid_creation,
    test_match_gap_empty_title_rejected,
    test_match_gap_invalid_severity_type_rejected,
    test_match_gap_to_dict,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 6. DimensionBreakdown Tests
# ---------------------------------------------------------------------------

print("\n=== 6. DimensionBreakdown Tests ===")


def test_dimension_breakdown_valid_creation():
    db = DimensionBreakdown(
        dimension=MatchDimension.TECHNOLOGY,
        raw_score=0.8,
        weighted_score=0.24,
        strengths=[_make_strength()],
        gaps=[_make_gap()],
        narrative="Good tech match.",
    )
    assert db.raw_score == 0.8


def test_dimension_breakdown_invalid_score_rejected():
    _expect_raises(ValueError, lambda: DimensionBreakdown(
        dimension=MatchDimension.TECHNOLOGY,
        raw_score=1.5,
        weighted_score=0.24,
    ))


def test_dimension_breakdown_invalid_strengths_element_rejected():
    _expect_raises(TypeError, lambda: DimensionBreakdown(
        dimension=MatchDimension.TECHNOLOGY,
        raw_score=0.8,
        weighted_score=0.24,
        strengths=["not a MatchStrength"],
    ))


def test_dimension_breakdown_to_dict():
    db = DimensionBreakdown(
        dimension=MatchDimension.DOMAIN,
        raw_score=0.5,
        weighted_score=0.075,
    )
    d = db.to_dict()
    assert d["dimension"] == "DOMAIN"
    json.dumps(d)


for fn in [
    test_dimension_breakdown_valid_creation,
    test_dimension_breakdown_invalid_score_rejected,
    test_dimension_breakdown_invalid_strengths_element_rejected,
    test_dimension_breakdown_to_dict,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 7. MatchExplanation Tests
# ---------------------------------------------------------------------------

print("\n=== 7. MatchExplanation Tests ===")


def test_match_explanation_valid_creation():
    me = _make_explanation()
    assert len(me.strengths) == 1
    assert len(me.gaps) == 2


def test_match_explanation_critical_gap_count():
    me = MatchExplanation(
        gaps=[
            _make_gap(GapSeverity.CRITICAL),
            _make_gap(GapSeverity.CRITICAL),
            _make_gap(GapSeverity.HIGH),
        ]
    )
    assert me.critical_gap_count == 2


def test_match_explanation_high_gap_count():
    me = MatchExplanation(
        gaps=[
            _make_gap(GapSeverity.CRITICAL),
            _make_gap(GapSeverity.HIGH),
        ]
    )
    assert me.high_gap_count == 1


def test_match_explanation_empty_valid():
    me = MatchExplanation()
    assert me.strengths == []
    assert me.gaps == []
    assert me.critical_gap_count == 0


def test_match_explanation_invalid_strengths_element_rejected():
    _expect_raises(TypeError, lambda: MatchExplanation(
        strengths=["not a MatchStrength"],
    ))


def test_match_explanation_invalid_gaps_element_rejected():
    _expect_raises(TypeError, lambda: MatchExplanation(
        gaps=["not a MatchGap"],
    ))


def test_match_explanation_to_dict_json_serializable():
    d = _make_explanation().to_dict()
    assert "strengths" in d
    assert "gaps" in d
    assert "critical_gap_count" in d
    json.dumps(d)


for fn in [
    test_match_explanation_valid_creation,
    test_match_explanation_critical_gap_count,
    test_match_explanation_high_gap_count,
    test_match_explanation_empty_valid,
    test_match_explanation_invalid_strengths_element_rejected,
    test_match_explanation_invalid_gaps_element_rejected,
    test_match_explanation_to_dict_json_serializable,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 8. MatchResult Tests
# ---------------------------------------------------------------------------

print("\n=== 8. MatchResult Tests ===")


def test_match_result_valid_creation():
    r = _make_result()
    assert r.candidate_id == _CAND_ID
    assert r.drive_id == _DRIVE_ID
    assert isinstance(r.match_tier, MatchTier)
    assert r.match_tier == MatchTier.STRONG  # score=0.75


def test_match_result_tier_derived_from_score():
    r = MatchResult(
        candidate_id=_CAND_ID,
        drive_id=_DRIVE_ID,
        score=MatchScore.zero(),
        explanation=MatchExplanation(),
    )
    assert r.match_tier == MatchTier.WEAK


def test_match_result_excellent_tier():
    r = MatchResult(
        candidate_id=_CAND_ID,
        drive_id=_DRIVE_ID,
        score=_make_match_score(0.90),
        explanation=MatchExplanation(),
    )
    assert r.match_tier == MatchTier.EXCELLENT


def test_match_result_invalid_candidate_id_rejected():
    _expect_raises(ValueError, lambda: MatchResult(
        candidate_id="not-a-uuid",
        drive_id=_DRIVE_ID,
        score=_make_match_score(),
        explanation=MatchExplanation(),
    ))


def test_match_result_invalid_drive_id_rejected():
    _expect_raises(ValueError, lambda: MatchResult(
        candidate_id=_CAND_ID,
        drive_id="not-a-uuid",
        score=_make_match_score(),
        explanation=MatchExplanation(),
    ))


def test_match_result_invalid_score_type_rejected():
    _expect_raises(TypeError, lambda: MatchResult(
        candidate_id=_CAND_ID,
        drive_id=_DRIVE_ID,
        score={"overall_score": 0.5},  # dict instead of MatchScore
        explanation=MatchExplanation(),
    ))


def test_match_result_generated_at_is_utc():
    r = _make_result()
    assert r.generated_at.tzinfo is not None


def test_match_result_to_dict_json_serializable():
    d = _make_result().to_dict()
    assert "candidate_id" in d
    assert "drive_id" in d
    assert "match_tier" in d
    assert "score" in d
    assert "explanation" in d
    assert "generated_at" in d
    json.dumps(d)


def test_match_result_to_dict_contains_tier_value():
    d = _make_result().to_dict()
    assert d["match_tier"] == "STRONG"


for fn in [
    test_match_result_valid_creation,
    test_match_result_tier_derived_from_score,
    test_match_result_excellent_tier,
    test_match_result_invalid_candidate_id_rejected,
    test_match_result_invalid_drive_id_rejected,
    test_match_result_invalid_score_type_rejected,
    test_match_result_generated_at_is_utc,
    test_match_result_to_dict_json_serializable,
    test_match_result_to_dict_contains_tier_value,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 9. MatchingWeights Tests
# ---------------------------------------------------------------------------

print("\n=== 9. MatchingWeights Tests ===")


def test_matching_weights_default_valid():
    w = MatchingWeights.default()
    assert len(w.weights) == 6
    assert w.get_weight(MatchDimension.TECHNOLOGY) == 0.30


def test_matching_weights_normalized_sums_to_one():
    w = MatchingWeights.default()
    n = w.normalized()
    assert abs(sum(n.values()) - 1.0) < 1e-9


def test_matching_weights_missing_dimension_rejected():
    incomplete = {
        MatchDimension.TECHNOLOGY.value: 0.5,
        MatchDimension.COMPETENCY.value: 0.5,
        # DOMAIN, SIGNAL, PROJECT, BEHAVIORAL missing
    }
    _expect_raises(KeyError, lambda: MatchingWeights(weights=incomplete))


def test_matching_weights_zero_weight_rejected():
    bad = {d.value: 0.1 for d in MatchDimension}
    bad[MatchDimension.TECHNOLOGY.value] = 0.0
    _expect_raises(ValueError, lambda: MatchingWeights(weights=bad))


def test_matching_weights_negative_weight_rejected():
    bad = {d.value: 0.1 for d in MatchDimension}
    bad[MatchDimension.SIGNAL.value] = -0.1
    _expect_raises(ValueError, lambda: MatchingWeights(weights=bad))


def test_matching_weights_with_overrides_valid():
    w  = MatchingWeights.default()
    w2 = w.with_overrides(
        {MatchDimension.TECHNOLOGY.value: 0.50},
        new_version="custom_v1",
    )
    assert w2.get_weight(MatchDimension.TECHNOLOGY) == 0.50
    assert w2.version == "custom_v1"
    # Original unchanged
    assert w.get_weight(MatchDimension.TECHNOLOGY) == 0.30


def test_matching_weights_with_overrides_invalid_key_rejected():
    w = MatchingWeights.default()
    _expect_raises(ValueError, lambda: w.with_overrides({"INVALID_DIM": 0.5}))


def test_matching_weights_get_weight_invalid_type_rejected():
    w = MatchingWeights.default()
    _expect_raises(TypeError, lambda: w.get_weight("TECHNOLOGY"))


def test_matching_weights_to_dict_json_serializable():
    d = MatchingWeights.default().to_dict()
    assert "weights" in d
    assert "version" in d
    json.dumps(d)


for fn in [
    test_matching_weights_default_valid,
    test_matching_weights_normalized_sums_to_one,
    test_matching_weights_missing_dimension_rejected,
    test_matching_weights_zero_weight_rejected,
    test_matching_weights_negative_weight_rejected,
    test_matching_weights_with_overrides_valid,
    test_matching_weights_with_overrides_invalid_key_rejected,
    test_matching_weights_get_weight_invalid_type_rejected,
    test_matching_weights_to_dict_json_serializable,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 10. MatchingRequest Tests
# ---------------------------------------------------------------------------

print("\n=== 10. MatchingRequest Tests ===")


def test_matching_request_valid_creation():
    r = MatchingRequest(
        candidate_id=_CAND_ID,
        drive_id=_DRIVE_ID,
    )
    assert r.weights_version == "default_v1"
    assert r.requested_by == "system"


def test_matching_request_invalid_candidate_id_rejected():
    _expect_raises(ValueError, lambda: MatchingRequest(
        candidate_id="bad",
        drive_id=_DRIVE_ID,
    ))


def test_matching_request_empty_weights_version_rejected():
    _expect_raises(ValueError, lambda: MatchingRequest(
        candidate_id=_CAND_ID,
        drive_id=_DRIVE_ID,
        weights_version="",
    ))


def test_matching_request_empty_requested_by_rejected():
    _expect_raises(ValueError, lambda: MatchingRequest(
        candidate_id=_CAND_ID,
        drive_id=_DRIVE_ID,
        requested_by="   ",
    ))


def test_matching_request_to_dict():
    r = MatchingRequest(
        candidate_id=_CAND_ID,
        drive_id=_DRIVE_ID,
        weights_version="custom_v1",
        requested_by="admin_bulk",
    )
    d = r.to_dict()
    assert d["weights_version"] == "custom_v1"
    assert d["requested_by"] == "admin_bulk"
    json.dumps(d)


for fn in [
    test_matching_request_valid_creation,
    test_matching_request_invalid_candidate_id_rejected,
    test_matching_request_empty_weights_version_rejected,
    test_matching_request_empty_requested_by_rejected,
    test_matching_request_to_dict,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 11. Protocol Structural Tests
# ---------------------------------------------------------------------------

print("\n=== 11. Protocol Structural Tests ===")


def test_dimension_scorer_protocol_is_runtime_checkable():
    # Verify Protocol can be used with isinstance at runtime
    assert hasattr(DimensionScorer, "score")


def test_matching_engine_protocol_is_runtime_checkable():
    assert hasattr(MatchingEngine, "score_candidate_against_drive")
    assert hasattr(MatchingEngine, "score_drive_against_candidate")


def test_ranking_engine_protocol_is_runtime_checkable():
    assert hasattr(RankingEngine, "rank_candidates_for_drive")
    assert hasattr(RankingEngine, "rank_drives_for_candidate")


class _ConcreteScorer:
    """Minimal concrete implementation to verify Protocol structural matching."""
    def score(self, context) -> DimensionScore:
        return _make_dim_score()


def test_concrete_scorer_satisfies_protocol():
    scorer = _ConcreteScorer()
    assert isinstance(scorer, DimensionScorer)


for fn in [
    test_dimension_scorer_protocol_is_runtime_checkable,
    test_matching_engine_protocol_is_runtime_checkable,
    test_ranking_engine_protocol_is_runtime_checkable,
    test_concrete_scorer_satisfies_protocol,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# 12. Cross-Module Integration Tests
# ---------------------------------------------------------------------------

print("\n=== 12. Cross-Module Integration Tests ===")


def test_full_match_result_round_trip():
    """Construct a MatchResult and verify full to_dict() round trip."""
    r = _make_result()
    d = r.to_dict()

    # Verify nested serialization
    assert d["score"]["overall_score"] == 0.75
    assert d["explanation"]["critical_gap_count"] == 1
    assert d["explanation"]["high_gap_count"] == 1
    assert d["match_tier"] == "STRONG"

    # Verify it is fully JSON serializable
    json_str = json.dumps(d)
    reloaded = json.loads(json_str)
    assert reloaded["match_tier"] == "STRONG"


def test_match_score_zero_produces_weak_tier():
    r = MatchResult(
        candidate_id=_CAND_ID,
        drive_id=_DRIVE_ID,
        score=MatchScore.zero(),
        explanation=MatchExplanation(),
    )
    assert r.match_tier == MatchTier.WEAK
    d = r.to_dict()
    assert d["match_tier"] == "WEAK"


def test_weights_normalized_used_in_context():
    """Verify that MatchingWeights.normalized() produces valid proportions."""
    w = MatchingWeights.default()
    n = w.normalized()
    assert len(n) == 6
    assert all(v > 0 for v in n.values())
    assert abs(sum(n.values()) - 1.0) < 1e-9


for fn in [
    test_full_match_result_round_trip,
    test_match_score_zero_produces_weak_tier,
    test_weights_normalized_used_in_context,
]:
    _run(fn.__name__, fn)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

total = _pass_count + _fail_count
print(f"\n{'='*55}")
print(f"Phase 5.1 Test Results: {_pass_count}/{total} passed")
if _fail_count == 0:
    print("STATUS: ALL TESTS PASSED — PHASE 5.1 COMPLETE")
else:
    print(f"STATUS: {_fail_count} TEST(S) FAILED")
print(f"{'='*55}")

if _fail_count > 0:
    sys.exit(1)
