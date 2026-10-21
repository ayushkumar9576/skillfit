"""
scripts/test_phase5_scoring_repair.py
--------------------------------------
Comprehensive Regression Test Suite for Phase 5 Matching Engine Scoring Repair.
Validates Tests A through K covering:
  - Test A: Strong candidate match
  - Test B: Partial candidate match
  - Test C: Weak candidate match
  - Test D: Semantic equivalence (e.g., python3 -> python, postgres -> postgresql)
  - Test E: Keyword stuffing resistance
  - Test F: Missing information robustness
  - Test G: Vector correctness & edge cases
  - Test H: Score mathematics & reconciliation
  - Test I: Ranking consistency & tie-breaking
  - Test J: End-to-end recommendation service integration
  - Test K: Live Google1 benchmark scenario
"""

import sys
import uuid
import math
import datetime
from typing import Dict, List, Any

from app.matching.enums import MatchDimension, MatchTier, GapSeverity
from app.matching.models.weights import MatchingWeights
from app.matching.models.scores import MatchScore, DimensionScore
from app.matching.models.explanation import MatchExplanation, MatchStrength, MatchGap, DimensionBreakdown
from app.matching.models.result import MatchResult
from app.matching.vectorization.schema import CandidateVectorPayload, DriveVectorPayload, VECTOR_SCHEMA_VERSION
from app.matching.vectorization.canon import normalize_technology_name
from app.matching.similarity.cosine_similarity import calculate_cosine_similarity
from app.matching.similarity.penalty_engine import calculate_penalty
from app.matching.similarity.matching_engine import match, _flatten_vector, adjust_match_score
from app.models.candidate_vector import CandidateVectorModel
from app.models.drive_vector import DriveVectorModel


def create_test_candidate(
    techs: Dict[str, float] = None,
    comps: Dict[str, float] = None,
    doms: Dict[str, float] = None,
    sigs: Dict[str, float] = None,
    proj_score: float = 0.5,
    resume_id: str = None
) -> CandidateVectorModel:
    r_id = uuid.UUID(resume_id) if resume_id else uuid.uuid4()
    return CandidateVectorModel(
        id=uuid.uuid4(),
        resume_id=r_id,
        schema_version=VECTOR_SCHEMA_VERSION,
        vector_json={
            "schema_version": VECTOR_SCHEMA_VERSION,
            "technologies": techs or {},
            "competencies": comps or {},
            "domains": doms or {},
            "signals": sigs or {},
            "project_score": proj_score
        },
        updated_at=datetime.datetime.now(datetime.timezone.utc)
    )


def create_test_drive(
    techs: Dict[str, float] = None,
    comps: Dict[str, float] = None,
    doms: Dict[str, float] = None,
    sigs: Dict[str, float] = None,
    crits: List[str] = None,
    drive_id: str = None
) -> DriveVectorModel:
    d_id = uuid.UUID(drive_id) if drive_id else uuid.uuid4()
    return DriveVectorModel(
        id=uuid.uuid4(),
        drive_id=d_id,
        schema_version=VECTOR_SCHEMA_VERSION,
        vector_json={
            "schema_version": VECTOR_SCHEMA_VERSION,
            "technologies": techs or {},
            "competencies": comps or {},
            "domains": doms or {},
            "signals": sigs or {},
            "critical_requirements": crits or []
        },
        updated_at=datetime.datetime.now(datetime.timezone.utc)
    )


# ---------------------------------------------------------------------------
# Test Suites
# ---------------------------------------------------------------------------

def test_a_strong_candidate_match():
    print("--- Test A: Strong Candidate Match ---")
    drive = create_test_drive(
        techs={"python": 1.0, "fastapi": 0.75, "postgresql": 0.75},
        comps={"BACKEND_DEVELOPMENT": 1.0, "API_DEVELOPMENT": 1.0, "DATABASE_DESIGN": 0.75},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"STRONG_PROJECTS": 1.0, "DEVELOPMENT_FOCUSED": 1.0},
        crits=["tech:python", "comp:BACKEND_DEVELOPMENT"]
    )
    cand_strong = create_test_candidate(
        techs={"python": 0.9, "fastapi": 0.8, "postgresql": 0.8},
        comps={"BACKEND_DEVELOPMENT": 0.9, "API_DEVELOPMENT": 0.8, "DATABASE_DESIGN": 0.8},
        doms={"SOFTWARE_ENGINEERING": 1.0, "BACKEND": 1.0},
        sigs={"STRONG_PROJECTS": 1.0, "DEVELOPMENT_FOCUSED": 1.0, "OWNED": 1.0},
        proj_score=0.85
    )
    result = match(cand_strong, drive)
    assert result.score.overall_score >= 0.75, f"Expected strong match >= 0.75, got {result.score.overall_score}"
    assert result.match_tier in (MatchTier.STRONG, MatchTier.EXCELLENT)
    assert result.explanation.critical_gap_count == 0
    assert len(result.explanation.strengths) >= 2
    print(f"PASS: Strong candidate scored {result.score.overall_score:.4f} ({result.match_tier.value})")


def test_b_partial_candidate_match():
    print("\n--- Test B: Partial Candidate Match ---")
    drive = create_test_drive(
        techs={"python": 1.0, "fastapi": 0.75, "postgresql": 0.75, "docker": 0.75},
        comps={"BACKEND_DEVELOPMENT": 1.0, "API_DEVELOPMENT": 1.0, "DATABASE_DESIGN": 0.75},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"STRONG_PROJECTS": 1.0, "DEVELOPMENT_FOCUSED": 1.0},
        crits=["tech:python", "tech:postgresql"]
    )
    # Candidate meets python and backend, but lacks postgresql (critical gap) and docker
    cand_partial = create_test_candidate(
        techs={"python": 0.7, "flask": 0.5},
        comps={"BACKEND_DEVELOPMENT": 0.7},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"DEVELOPMENT_FOCUSED": 0.7},
        proj_score=0.45
    )
    result = match(cand_partial, drive)
    assert 0.40 <= result.score.overall_score < 0.70, f"Expected intermediate score (0.40 - 0.70), got {result.score.overall_score}"
    assert result.match_tier in (MatchTier.PARTIAL, MatchTier.MODERATE)
    # Check that gaps were identified
    gap_titles = [g.title.lower() for g in result.explanation.gaps]
    assert any("postgresql" in g or "docker" in g for g in gap_titles)
    print(f"PASS: Partial candidate scored {result.score.overall_score:.4f} ({result.match_tier.value}) with correct gaps")



def test_c_weak_candidate_match():
    print("\n--- Test C: Weak Candidate Match ---")
    drive = create_test_drive(
        techs={"python": 1.0, "fastapi": 0.75, "postgresql": 0.75},
        comps={"BACKEND_DEVELOPMENT": 1.0, "API_DEVELOPMENT": 1.0},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        crits=["tech:python", "comp:BACKEND_DEVELOPMENT"]
    )
    # Candidate is purely frontend/design with no python and no backend
    cand_weak = create_test_candidate(
        techs={"figma": 0.8, "photoshop": 0.8, "css": 0.6},
        comps={"UI_DESIGN": 0.8},
        doms={"DESIGN": 1.0},
        sigs={},
        proj_score=0.2
    )
    result = match(cand_weak, drive)
    assert result.score.overall_score < 0.30, f"Expected weak score < 0.30, got {result.score.overall_score}"
    assert result.match_tier == MatchTier.WEAK
    assert result.explanation.critical_gap_count >= 1
    print(f"PASS: Weak candidate scored {result.score.overall_score:.4f} ({result.match_tier.value})")


def test_d_semantic_equivalence():
    print("\n--- Test D: Semantic Equivalence ---")
    drive = create_test_drive(
        techs={"python": 1.0, "postgresql": 0.75},
        comps={"BACKEND_DEVELOPMENT": 1.0},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        crits=["tech:python"]
    )
    # Candidate 1 lists 'python' and 'postgresql'
    c1 = create_test_candidate(
        techs={"python": 0.8, "postgresql": 0.8},
        comps={"BACKEND_DEVELOPMENT": 0.8},
        doms={"SOFTWARE_ENGINEERING": 1.0}
    )
    # Candidate 2 lists 'python3' and 'postgres' (which normalize to python and postgresql)
    c2 = create_test_candidate(
        techs={normalize_technology_name("python3"): 0.8, normalize_technology_name("postgres"): 0.8},
        comps={"BACKEND_DEVELOPMENT": 0.8},
        doms={"BACKEND": 1.0, "SOFTWARE_ENGINEERING": 1.0}
    )
    r1 = match(c1, drive)
    r2 = match(c2, drive)
    assert math.isclose(r1.score.overall_score, r2.score.overall_score, abs_tol=1e-3)
    assert r2.explanation.critical_gap_count == 0
    print(f"PASS: Semantic equivalence recognized: C1={r1.score.overall_score:.4f}, C2={r2.score.overall_score:.4f}")


def test_e_irrelevant_keyword_stuffing():
    print("\n--- Test E: Irrelevant Keyword Stuffing ---")
    drive = create_test_drive(
        techs={"python": 1.0, "fastapi": 0.75, "postgresql": 0.75},
        comps={"BACKEND_DEVELOPMENT": 1.0, "API_DEVELOPMENT": 1.0},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"STRONG_PROJECTS": 1.0},
        crits=["tech:python", "comp:BACKEND_DEVELOPMENT"]
    )
    # Candidate with verified deep evidence
    c_genuine = create_test_candidate(
        techs={"python": 0.9, "fastapi": 0.8, "postgresql": 0.8},
        comps={"BACKEND_DEVELOPMENT": 0.9, "API_DEVELOPMENT": 0.8},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"STRONG_PROJECTS": 1.0, "DEVELOPMENT_FOCUSED": 1.0, "OWNED": 1.0},
        proj_score=0.85
    )
    # Candidate who stuffed 30 keywords at CLAIMED level (0.2), 0 project score, 0 ownership
    stuffed_techs = {k: 0.2 for k in ["python", "fastapi", "postgresql", "java", "c++", "ruby", "rust", "php", "go", "swift", "kotlin", "scala"]}
    c_stuffed = create_test_candidate(
        techs=stuffed_techs,
        comps={"BACKEND_DEVELOPMENT": 0.2},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={},
        proj_score=0.0
    )
    r_genuine = match(c_genuine, drive)
    r_stuffed = match(c_stuffed, drive)
    assert r_genuine.score.overall_score > r_stuffed.score.overall_score + 0.30, \
        f"Genuine candidate ({r_genuine.score.overall_score:.3f}) should significantly beat stuffed candidate ({r_stuffed.score.overall_score:.3f})"
    print(f"PASS: Keyword stuffing prevented: Genuine={r_genuine.score.overall_score:.4f} vs Stuffed={r_stuffed.score.overall_score:.4f}")


def test_f_missing_information_robustness():
    print("\n--- Test F: Missing Information Robustness ---")
    drive = create_test_drive(
        techs={"python": 1.0},
        comps={},
        doms={},
        sigs={},
        crits=[]
    )
    # Candidate with empty dicts for optional fields
    c_empty = create_test_candidate(techs={}, comps={}, doms={}, sigs={}, proj_score=0.0)
    res = match(c_empty, drive)
    assert res.score.raw_score == 0.0
    assert res.score.overall_score == 0.15  # 0.0 calibrated to 15% morale boost floor
    assert res.match_tier == MatchTier.WEAK
    assert res.score.coverage_ratio > 0.0
    print("PASS: Empty candidate information handled safely without crashes")


def test_g_vector_correctness():
    print("\n--- Test G: Vector Correctness & Edge Cases ---")
    # Identical vectors
    v1 = {"a": 1.0, "b": 0.5}
    assert math.isclose(calculate_cosine_similarity(v1, v1), 1.0, rel_tol=1e-5)
    # Orthogonal vectors
    v2 = {"c": 1.0}
    assert calculate_cosine_similarity(v1, v2) == 0.0
    # Zero magnitude
    assert calculate_cosine_similarity({"a": 0.0}, {"a": 0.0}) == 0.0
    # Empty
    assert calculate_cosine_similarity({}, {"a": 1.0}) == 0.0
    print("PASS: Vector similarity calculations mathematically correct for all edge cases")


def test_h_score_mathematics_and_reconciliation():
    print("\n--- Test H: Score Mathematics & Reconciliation ---")
    drive = create_test_drive(
        techs={"python": 1.0, "fastapi": 0.5},
        comps={"BACKEND_DEVELOPMENT": 1.0},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"STRONG_PROJECTS": 1.0},
        crits=["tech:python"]
    )
    cand = create_test_candidate(
        techs={"python": 0.8, "fastapi": 0.6},
        comps={"BACKEND_DEVELOPMENT": 0.8},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"STRONG_PROJECTS": 1.0},
        proj_score=0.75
    )
    result = match(cand, drive)
    dim_scores = result.score.dimension_scores
    
    # Verify that sum of weighted dimension scores reconciles with overall_score
    active_weights_sum = sum(ds.weight for ds in dim_scores.values())
    calculated_base_score = sum(ds.raw_score * (ds.weight / active_weights_sum) for ds in dim_scores.values())
    
    # No critical missing items for this candidate
    penalty = calculate_penalty(_flatten_vector(CandidateVectorPayload(**cand.vector_json), is_candidate=True), DriveVectorPayload(**drive.vector_json))
    expected_final = calculated_base_score * penalty.multiplier
    expected_boosted = adjust_match_score(expected_final * 100.0) / 100.0
    
    assert math.isclose(result.score.raw_score, expected_final, abs_tol=1e-4), \
        f"Reconciliation error on raw_score: raw={result.score.raw_score}, expected={expected_final}"
    assert math.isclose(result.score.overall_score, expected_boosted, abs_tol=1e-3), \
        f"Reconciliation error on overall_score: overall={result.score.overall_score}, expected={expected_boosted}"
    
    # Verify DimensionScore bounds
    for d_name, ds in dim_scores.items():
        assert 0.0 <= ds.raw_score <= 1.0
        assert 0.0 <= ds.weighted_score <= 1.0
        assert ds.weight > 0.0
        assert ds.matched_items <= ds.total_items
        
    print(f"PASS: Score mathematics reconciled 100%: calculated={calculated_base_score:.4f}, final={result.score.overall_score:.4f}")


def test_i_ranking_consistency():
    print("\n--- Test I: Ranking Consistency ---")
    drive = create_test_drive(
        techs={"python": 1.0, "postgresql": 0.8, "docker": 0.6},
        comps={"BACKEND_DEVELOPMENT": 1.0, "API_DEVELOPMENT": 0.8},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"STRONG_PROJECTS": 1.0},
        crits=["tech:python", "comp:BACKEND_DEVELOPMENT"]
    )
    
    c_strong = create_test_candidate(
        techs={"python": 0.9, "postgresql": 0.9, "docker": 0.8},
        comps={"BACKEND_DEVELOPMENT": 0.9, "API_DEVELOPMENT": 0.9},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"STRONG_PROJECTS": 1.0, "DEVELOPMENT_FOCUSED": 1.0},
        proj_score=0.85
    )
    c_moderate = create_test_candidate(
        techs={"python": 0.6, "postgresql": 0.4},
        comps={"BACKEND_DEVELOPMENT": 0.6},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={"DEVELOPMENT_FOCUSED": 0.7},
        proj_score=0.50
    )
    c_weak = create_test_candidate(
        techs={"ruby": 0.8},
        comps={},
        doms={"SOFTWARE_ENGINEERING": 1.0},
        sigs={},
        proj_score=0.20
    )
    
    r_strong = match(c_strong, drive)
    r_moderate = match(c_moderate, drive)
    r_weak = match(c_weak, drive)
    
    assert r_strong.score.overall_score > r_moderate.score.overall_score > r_weak.score.overall_score
    assert r_strong.match_tier in (MatchTier.STRONG, MatchTier.EXCELLENT)
    assert r_moderate.match_tier in (MatchTier.PARTIAL, MatchTier.MODERATE, MatchTier.STRONG)
    assert r_weak.match_tier == MatchTier.WEAK
    print(f"PASS: Ranking consistent: Strong ({r_strong.score.overall_score:.3f}) > Moderate ({r_moderate.score.overall_score:.3f}) > Weak ({r_weak.score.overall_score:.3f})")



def test_j_end_to_end_recommendation_service():
    print("\n--- Test J: End-to-End Recommendation Service ---")
    from app.matching.services.recommendation_service import RecommendationService
    
    # Test using mock DB
    class MockQuery:
        def __init__(self, items): self.items = items
        def filter(self, *args): return self
        def all(self): return self.items
        
    drive = create_test_drive(techs={"python": 1.0}, crits=["tech:python"])
    cand1 = create_test_candidate(techs={"python": 1.0}, proj_score=0.9)
    cand2 = create_test_candidate(techs={"python": 0.5}, proj_score=0.4)
    
    class MockDB:
        def query(self, model):
            if model == DriveVectorModel: return MockQuery([drive])
            if model == CandidateVectorModel: return MockQuery([cand1, cand2])
            return MockQuery([])
            
    db = MockDB()
    # Mock VectorPersistenceService
    from app.matching.services.vector_persistence_service import VectorPersistenceService
    VectorPersistenceService.get_drive_vector = staticmethod(lambda db, d_id: drive)
    VectorPersistenceService.get_candidate_vector = staticmethod(lambda db, r_id: cand1)
    
    results = RecommendationService.get_recommended_candidates(db, str(drive.drive_id))
    assert len(results) == 2
    assert results[0].candidate_id == str(cand1.resume_id)
    assert results[0].score.overall_score >= results[1].score.overall_score
    print("PASS: RecommendationService ranks and returns expected candidates with explanations")


def test_k_live_google1_scenario():
    print("\n--- Test K: Live Google1 Scenario Verification ---")
    try:
        from app.db.database import SessionLocal
        from app.models.drive import Drive
        from app.models.drive_vector import DriveVectorModel
        from app.models.candidate_vector import CandidateVectorModel
        
        db = SessionLocal()
        google1 = db.query(Drive).filter(Drive.company_name.ilike('%Google1%')).first()
        if not google1:
            print("Google1 drive not found in DB; skipping live DB test.")
            db.close()
            return
            
        d_vec = db.query(DriveVectorModel).filter_by(drive_id=google1.id).first()
        assert d_vec is not None, "Google1 drive vector missing"
        
        rahul_id = "baf188bc-9f80-4d69-8c0d-416ae201a5bb"
        ayush_id = "8f69ebcb-3fa5-4bf3-bf9f-9a1636bc424a"
        
        c_rahul = db.query(CandidateVectorModel).filter_by(resume_id=rahul_id).first()
        c_ayush = db.query(CandidateVectorModel).filter_by(resume_id=ayush_id).first()
        
        assert c_rahul is not None and c_ayush is not None, "Candidate vectors missing"
        
        res_rahul = match(c_rahul, d_vec)
        res_ayush = match(c_ayush, d_vec)
        
        # Verify Rahul Sharma repaired score (73.9% boosted from 69.9% raw)
        assert res_rahul.score.overall_score >= 0.70, f"Rahul score should be >= 0.70, got {res_rahul.score.overall_score}"
        assert res_rahul.match_tier == MatchTier.STRONG
        assert res_rahul.explanation.critical_gap_count == 0
        
        # Verify Ayush Kumar repaired score (63.2% boosted from 54.5% raw)
        assert 0.55 <= res_ayush.score.overall_score < 0.70, f"Ayush score should be moderate (0.55 - 0.70), got {res_ayush.score.overall_score}"
        assert res_ayush.match_tier == MatchTier.MODERATE
        assert res_ayush.explanation.critical_gap_count == 0
        
        print(f"PASS: Live Google1 Scenario successfully verified:")
        print(f"  - Rahul Sharma (temp): {res_rahul.score.overall_score*100:.1f}% ({res_rahul.match_tier.value}) [Raw: {res_rahul.score.raw_score*100:.1f}%]")
        print(f"  - Ayush Kumar:         {res_ayush.score.overall_score*100:.1f}% ({res_ayush.match_tier.value}) [Raw: {res_ayush.score.raw_score*100:.1f}%]")
        db.close()
    except Exception as e:
        print(f"Error in Test K: {e}")
        raise


def run_all_tests():
    print("==================================================================")
    print("SKILLFIT PHASE 5 MATCHING ENGINE REGRESSION SUITE (TESTS A - K)")
    print("==================================================================")
    test_a_strong_candidate_match()
    test_b_partial_candidate_match()
    test_c_weak_candidate_match()
    test_d_semantic_equivalence()
    test_e_irrelevant_keyword_stuffing()
    test_f_missing_information_robustness()
    test_g_vector_correctness()
    test_h_score_mathematics_and_reconciliation()
    test_i_ranking_consistency()
    test_j_end_to_end_recommendation_service()
    test_k_live_google1_scenario()
    print("\n==================================================================")
    print("ALL 11 REGRESSION SUITES PASSED (TESTS A - K)")
    print("==================================================================")


if __name__ == "__main__":
    run_all_tests()
