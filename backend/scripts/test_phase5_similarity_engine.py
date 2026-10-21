import uuid
import math
from app.matching.similarity.cosine_similarity import calculate_cosine_similarity
from app.matching.similarity.penalty_engine import calculate_penalty
from app.matching.similarity.matching_engine import match
from app.matching.vectorization.schema import CandidateVectorPayload, DriveVectorPayload
from app.models.candidate_vector import CandidateVectorModel
from app.models.drive_vector import DriveVectorModel
from app.matching.enums import MatchTier

def test_cosine_similarity():
    print("--- Testing Cosine Similarity ---")
    
    # Identical vectors
    v1 = {"a": 1.0, "b": 0.5}
    import math
    assert math.isclose(calculate_cosine_similarity(v1, v1), 1.0, rel_tol=1e-5)
    print("Identical vectors: PASS")
    
    # Orthogonal vectors
    v2 = {"c": 1.0}
    assert calculate_cosine_similarity(v1, v2) == 0.0
    print("Orthogonal vectors: PASS")
    
    # Partial overlap
    v3 = {"a": 1.0, "c": 0.5}
    score = calculate_cosine_similarity(v1, v3)
    assert 0.0 < score < 1.0
    print(f"Partial overlap: PASS (Score={score:.3f})")
    
    # Empty vectors
    assert calculate_cosine_similarity({}, {"a": 1.0}) == 0.0
    print("Empty vectors: PASS")
    
    # Zero magnitude
    assert calculate_cosine_similarity({"a": 0.0}, {"a": 0.0}) == 0.0
    print("Zero magnitude: PASS")

def test_penalty_engine():
    print("\n--- Testing Penalty Engine ---")
    
    cand = CandidateVectorPayload(schema_version=1, technologies={"python": 0.0}, competencies={}, domains={}, signals={}, project_score=0.0)
    
    # 0 critical gaps
    drive0 = DriveVectorPayload(schema_version=1, technologies={"python": 0.5}, competencies={}, domains={}, signals={}, critical_requirements=[])
    res0 = calculate_penalty(cand_flat={"tech:python": 0.0}, drive_payload=drive0)
    assert res0.multiplier == 1.0
    print("0 critical gaps: PASS")
    
    # 1 critical gap
    drive1 = DriveVectorPayload(schema_version=1, technologies={"python": 1.0}, competencies={}, domains={}, signals={}, critical_requirements=["tech:python"])
    res1 = calculate_penalty(cand_flat={"tech:python": 0.0}, drive_payload=drive1)
    assert res1.multiplier == 0.85
    print("1 critical gap: PASS")
    
    # 2 critical gaps
    drive2 = DriveVectorPayload(schema_version=1, technologies={"python": 1.0, "java": 1.0}, competencies={}, domains={}, signals={}, critical_requirements=["tech:python", "tech:java"])
    res2 = calculate_penalty(cand_flat={"tech:python": 0.0, "tech:java": 0.0}, drive_payload=drive2)
    assert res2.multiplier == 0.70
    print("2 critical gaps: PASS")
    
    # 3+ critical gaps
    drive3 = DriveVectorPayload(schema_version=1, technologies={"python": 1.0, "java": 1.0, "c++": 1.0}, competencies={}, domains={}, signals={}, critical_requirements=["tech:python", "tech:java", "tech:c++"])
    res3 = calculate_penalty(cand_flat={"tech:python": 0.0, "tech:java": 0.0, "tech:c++": 0.0}, drive_payload=drive3)
    assert res3.multiplier == 0.55
    print("3+ critical gaps: PASS")
    
    # Future change of numeric weight does not break detection
    drive_future = DriveVectorPayload(schema_version=1, technologies={"python": 4.0}, competencies={}, domains={}, signals={}, critical_requirements=["tech:python"])
    res_future = calculate_penalty(cand_flat={"tech:python": 0.0}, drive_payload=drive_future)
    assert res_future.multiplier == 0.85
    print("Future numeric weight change: PASS")

def test_namespace_safety():
    print("\n--- Testing Namespace Safety ---")
    from app.matching.similarity.matching_engine import _flatten_vector
    from app.matching.vectorization.schema import CandidateVectorPayload
    payload = CandidateVectorPayload(schema_version=1, technologies={"python": 1.0}, competencies={"python": 1.0}, domains={"python": 1.0}, signals={"python": 1.0}, project_score=1.0)
    flat = _flatten_vector(payload, is_candidate=True)
    assert flat["tech:python"] == 1.0
    assert flat["comp:python"] == 1.0
    assert flat["domain:python"] == 1.0
    assert flat["signal:python"] == 1.0
    assert len(flat) == 4
    print("Namespace collisions prevented: PASS")

def test_score_scale_consistency():
    print("\n--- Testing Score Scale Consistency ---")
    assert MatchTier.from_score(0.0) == MatchTier.WEAK
    assert MatchTier.from_score(0.39) == MatchTier.WEAK
    assert MatchTier.from_score(0.40) == MatchTier.PARTIAL
    assert MatchTier.from_score(0.60) == MatchTier.MODERATE
    assert MatchTier.from_score(0.75) == MatchTier.STRONG
    assert MatchTier.from_score(0.90) == MatchTier.EXCELLENT
    assert MatchTier.from_score(1.0) == MatchTier.EXCELLENT
    print("Tier boundaries enforced on 0.0 to 1.0 scale: PASS")

def test_matching_engine():
    print("\n--- Testing Matching Engine ---")
    
    cand_uuid = uuid.uuid4()
    drive_uuid = uuid.uuid4()
    
    # Perfect match
    cand_perf = CandidateVectorModel(
        id=uuid.uuid4(), resume_id=cand_uuid, source_snapshot_id=uuid.uuid4(), schema_version=1,
        vector_json={"schema_version": 1, "technologies": {"python": 1.0}, "competencies": {"backend": 1.0}, "domains": {}, "signals": {}, "project_score": 1.0}
    )
    drive_perf = DriveVectorModel(
        id=uuid.uuid4(), drive_id=drive_uuid, source_snapshot_id=uuid.uuid4(), schema_version=1,
        vector_json={"schema_version": 1, "technologies": {"python": 1.0}, "competencies": {"backend": 1.0}, "domains": {}, "signals": {}, "critical_requirements": []}
    )
    
    res = match(cand_perf, drive_perf)
    print(f"Perfect match score: {res.score.overall_score}")
    assert math.isclose(res.score.overall_score, 1.0, rel_tol=1e-5)
    assert res.match_tier == MatchTier.EXCELLENT
    assert len(res.explanation.strengths) == 2
    assert len(res.explanation.gaps) == 0
    print("Perfect match: PASS")
    
    # Weak match
    cand_weak = CandidateVectorModel(
        id=uuid.uuid4(), resume_id=cand_uuid, source_snapshot_id=uuid.uuid4(), schema_version=1,
        vector_json={"schema_version": 1, "technologies": {"java": 0.5}, "competencies": {}, "domains": {}, "signals": {}, "project_score": 0.2}
    )
    drive_weak = DriveVectorModel(
        id=uuid.uuid4(), drive_id=drive_uuid, source_snapshot_id=uuid.uuid4(), schema_version=1,
        vector_json={"schema_version": 1, "technologies": {"python": 1.0}, "competencies": {"backend": 1.0}, "domains": {}, "signals": {}, "critical_requirements": ["tech:python", "comp:backend"]}
    )
    
    res = match(cand_weak, drive_weak)
    assert res.score.raw_score == 0.0 # 0.0 raw cosine
    assert res.score.overall_score == 0.15 # 0.0 boosted to 15% floor
    assert res.match_tier == MatchTier.WEAK
    assert len(res.explanation.strengths) == 0
    assert len(res.explanation.gaps) == 2
    print("Weak match: PASS")
    
    # Example Output JSON
    print("\n--- Example Output ---")
    # Simulate a STRONG match output similar to prompt request
    cand_strong = CandidateVectorModel(
        id=uuid.uuid4(), resume_id=cand_uuid, source_snapshot_id=uuid.uuid4(), schema_version=1,
        vector_json={"schema_version": 1, "technologies": {"python": 1.0, "fastapi": 1.0, "docker": 0.0}, "competencies": {}, "domains": {}, "signals": {}, "project_score": 1.0}
    )
    drive_strong = DriveVectorModel(
        id=uuid.uuid4(), drive_id=drive_uuid, source_snapshot_id=uuid.uuid4(), schema_version=1,
        vector_json={"schema_version": 1, "technologies": {"python": 1.0, "fastapi": 0.75, "docker": 1.0}, "competencies": {}, "domains": {}, "signals": {}, "critical_requirements": ["tech:python", "tech:docker"]}
    )
    res = match(cand_strong, drive_strong)
    
    # We guarantee a single canonical scale [0.0, 1.0] internally and externally
    example_json = {
        "score": round(res.score.overall_score, 3),
        "tier": f"{res.match_tier.value}_MATCH",
        "strengths": [s.title.replace("Strong ", "") for s in res.explanation.strengths],
        "gaps": [g.title.replace("Missing ", "") for g in res.explanation.gaps]
    }
    
    import json
    print(json.dumps(example_json, indent=2))

if __name__ == "__main__":
    test_cosine_similarity()
    test_penalty_engine()
    test_namespace_safety()
    test_score_scale_consistency()
    test_matching_engine()
