import uuid
import datetime
from typing import List, Any
from app.matching.models.result import MatchResult
from app.models.candidate_vector import CandidateVectorModel
from app.models.drive_vector import DriveVectorModel
from app.matching.services.recommendation_service import RecommendationService
from app.matching.services.vector_persistence_service import VectorPersistenceService
from app.matching.enums import MatchTier

# --- Mocking Infrastructure ---

class MockQuery:
    def __init__(self, data: List[Any]):
        self.data = data

    def filter(self, *args):
        # We will manually handle the filtering for schema_version in the mock
        # args[0] is typically Model.schema_version == value
        # This is a bit tricky to mock perfectly without SQLAlchemy, so we'll just
        # filter based on our knowledge of the test data.
        
        # We will just evaluate the binary expression manually if possible, or 
        # for these tests, we can just return a pre-filtered list if we configure the mock right.
        return self

    def all(self):
        return self.data

class MockDB:
    def __init__(self, drives=None, candidates=None):
        self.drives = drives or []
        self.candidates = candidates or []
        
    def query(self, model):
        if model == DriveVectorModel:
            return MockQuery(self.drives)
        if model == CandidateVectorModel:
            return MockQuery(self.candidates)
        return MockQuery([])

def mock_get_candidate_vector(db, resume_id):
    for c in db.candidates:
        if c.resume_id == resume_id:
            return c
    return None

def mock_get_drive_vector(db, drive_id):
    for d in db.drives:
        if d.drive_id == drive_id:
            return d
    return None

# Patch the service directly for testing
VectorPersistenceService.get_candidate_vector = mock_get_candidate_vector
VectorPersistenceService.get_drive_vector = mock_get_drive_vector

# We need to monkeypatch the db.query filter to actually filter by schema version
original_query = MockDB.query
def patched_query(self, model):
    q = original_query(self, model)
    original_filter = q.filter
    def mock_filter(*args):
        # args[0] is e.g. DriveVectorModel.schema_version == 1
        # We will just rely on the right side of the expression
        expr = args[0]
        # In a real SQLAlchemy mock, it's complex. Let's just filter it manually by schema_version.
        # We extract the right side value from the expression.
        try:
            val = expr.right.value
            filtered_data = [x for x in q.data if x.schema_version == val]
            return MockQuery(filtered_data)
        except:
            return q
    q.filter = mock_filter
    return q
MockDB.query = patched_query

def create_cand(score=1.0, schema=1, tech=None, gaps_mock=0, date=None):
    if tech is None:
        tech = {"python": 1.0}
    c = CandidateVectorModel(
        id=uuid.uuid4(),
        resume_id=uuid.uuid4(),
        schema_version=schema,
        vector_json={
            "schema_version": schema,
            "technologies": tech,
            "competencies": {},
            "domains": {},
            "signals": {},
            "project_score": score
        },
        updated_at=date or datetime.datetime.now(datetime.timezone.utc)
    )
    return c

def create_drive(schema=1, tech=None, crit=None, date=None):
    if tech is None:
        tech = {"python": 1.0}
    if crit is None:
        crit = ["tech:python"]
    d = DriveVectorModel(
        id=uuid.uuid4(),
        drive_id=uuid.uuid4(),
        schema_version=schema,
        vector_json={
            "schema_version": schema,
            "technologies": tech,
            "competencies": {},
            "domains": {},
            "signals": {},
            "critical_requirements": crit
        },
        updated_at=date or datetime.datetime.now(datetime.timezone.utc)
    )
    return d

def test_candidate_to_drives():
    print("--- Test 1: Candidate -> Drives ---")
    cand = create_cand()
    
    # 3 drives with different scores
    d1 = create_drive(tech={"python": 1.0}) # Perfect match
    d2 = create_drive(tech={"java": 1.0}, crit=["tech:java"]) # 0 match, 1 critical gap
    d3 = create_drive(tech={"python": 0.5, "java": 1.0}, crit=["tech:java"]) # Partial match, 1 critical gap
    
    db = MockDB(drives=[d2, d3, d1], candidates=[cand])
    results = RecommendationService.get_recommended_drives(db, str(cand.resume_id))
    
    assert len(results) == 3
    # Order should be d1 (highest score), d3, d2
    assert results[0].drive_id == str(d1.drive_id)
    assert results[1].drive_id == str(d3.drive_id)
    assert results[2].drive_id == str(d2.drive_id)
    print("PASS: Candidate to Drives sorted correctly.")

def test_drive_to_candidates():
    print("\n--- Test 2: Drive -> Candidates ---")
    drive = create_drive(tech={"python": 1.0, "java": 1.0}, crit=["tech:python", "tech:java"])
    
    c1 = create_cand(tech={"python": 1.0, "java": 1.0}) # 1.0 score, 0 critical gaps
    c2 = create_cand(tech={"python": 1.0, "java": 0.0}) # 0.5 score, 1 critical gap
    c3 = create_cand(tech={"ruby": 1.0}) # 0.0 score, 2 critical gaps
    c4 = create_cand(tech={"python": 1.0, "java": 0.0}, score=0.9) # 0.5 score, 1 critical gap, higher project
    c5 = create_cand(tech={"python": 1.0, "java": 1.0}, score=0.5) # 1.0 score, 0 critical gaps, lower project
    
    db = MockDB(candidates=[c3, c2, c5, c4, c1], drives=[drive])
    results = RecommendationService.get_recommended_candidates(db, str(drive.drive_id))
    
    assert len(results) == 5
    # c1 (score 1.0, 0 gaps, project 1.0) -> rank 1
    # c5 (score 1.0, 0 gaps, project 0.5) -> rank 2
    # c4 (score 0.5, 1 gap, project 0.9) -> rank 3
    # c2 (score 0.5, 1 gap, project 1.0 (default)) -> Wait, c2 has project 1.0, c4 has 0.9.
    # Ah, c2 default score is 1.0. So c2 beats c4.
    # Let's adjust c2 to have project 0.2
    c2.vector_json["project_score"] = 0.2
    # Now order: c1, c5, c4, c2, c3
    
    # Run again with adjusted c2
    results = RecommendationService.get_recommended_candidates(db, str(drive.drive_id))
    assert results[0].candidate_id == str(c1.resume_id)
    assert results[1].candidate_id == str(c5.resume_id)
    assert results[2].candidate_id == str(c4.resume_id)
    assert results[3].candidate_id == str(c2.resume_id)
    assert results[4].candidate_id == str(c3.resume_id)
    print("PASS: Drive to Candidates sorted correctly.")

def test_schema_mismatch():
    print("\n--- Test 3: Schema Mismatch ---")
    cand = create_cand(schema=1)
    drive = create_drive(schema=2)
    
    # In db, filter will exclude drive. But let's inject it into the pipeline directly to test the ValueError safety net.
    # The requirement says: "Before every comparison: candidate.schema_version == drive.schema_version. If not: raise ValueError(...)"
    db = MockDB(drives=[drive], candidates=[cand])
    
    # We want to force the mismatched drive to be returned by the query
    original_query = db.query
    def broken_query(model):
        q = original_query(model)
        q.filter = lambda *args: MockQuery([drive]) if model == DriveVectorModel else q
        return q
    db.query = broken_query
    
    try:
        RecommendationService.get_recommended_drives(db, str(cand.resume_id))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Schema version mismatch" in str(e)
        print("PASS: Schema mismatch correctly raises ValueError.")

def test_empty_vectors():
    print("\n--- Test 4: Empty Vectors Table ---")
    cand = create_cand()
    db = MockDB(candidates=[cand], drives=[])
    res = RecommendationService.get_recommended_drives(db, str(cand.resume_id))
    assert res == []
    print("PASS: Empty drives returns []")
    
    drive = create_drive()
    db2 = MockDB(candidates=[], drives=[drive])
    res2 = RecommendationService.get_recommended_candidates(db2, str(drive.drive_id))
    assert res2 == []
    print("PASS: Empty candidates returns []")

def test_tie_breaking():
    print("\n--- Test 5: Tie-breaking ---")
    # Same score, same gaps, same project score. Newer date wins.
    d1 = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    d2 = datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc)
    
    drive = create_drive()
    c_old = create_cand(date=d1)
    c_new = create_cand(date=d2)
    
    db = MockDB(candidates=[c_old, c_new], drives=[drive])
    results = RecommendationService.get_recommended_candidates(db, str(drive.drive_id))
    
    assert results[0].candidate_id == str(c_new.resume_id)
    assert results[1].candidate_id == str(c_old.resume_id)
    print("PASS: Tie-breaking is deterministic based on updated_at.")

def test_explanation_generation():
    print("\n--- Test 6: Explanation Generation ---")
    cand = create_cand(score=0.9, tech={"python": 1.0, "fastapi": 1.0})
    drive = create_drive(tech={"python": 1.0, "fastapi": 1.0, "docker": 1.0}, crit=["tech:python", "tech:docker"])
    
    db = MockDB(candidates=[cand], drives=[drive])
    res = RecommendationService.get_recommended_drives(db, str(cand.resume_id))
    
    match_result = res[0]
    expl = match_result.explanation
    
    assert len(expl.strengths) == 2
    assert "python" in expl.strengths[0].title.lower() or "fastapi" in expl.strengths[0].title.lower()
    
    assert len(expl.gaps) == 1
    assert "docker" in expl.gaps[0].title.lower()
    
    # Narrative check
    assert expl.overall_narrative != ""
    assert "Strong alignment in" in expl.overall_narrative
    assert "Project sophistication exceeds expectations" in expl.overall_narrative
    assert "Missing" in expl.overall_narrative
    assert "docker" in expl.overall_narrative.lower()
    
    print("PASS: Explanations generated deterministically without LLM.")
    print("Narrative Output:", expl.overall_narrative)

if __name__ == "__main__":
    test_candidate_to_drives()
    test_drive_to_candidates()
    test_schema_mismatch()
    test_empty_vectors()
    test_tie_breaking()
    test_explanation_generation()
