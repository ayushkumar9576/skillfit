"""
scripts/test_readiness_pipeline.py
----------------------------------
Test script for Phase 3.11 Readiness Engine
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analysis.engines.readiness_engine import ReadinessEngine
from app.analysis.models.readiness_models import (
    ReadinessLevel, AnalysisStatus, Severity, DEPTH_ADVANCED, DEPTH_BEGINNER
)
from app.analysis.models.project_models import (
    ProjectAnalysisResult, ProjectIntelligenceReport, ScoredDimension as ProjScoredDimension
)
from app.analysis.models.skill_models import (
    SkillAnalysisResult, SkillProfile
)

def run_tests():
    engine = ReadinessEngine()
    print("Testing empty input...")
    result = engine.analyze("t1", None, None, None, None)
    assert result.readiness_score == 0.0
    assert result.analysis_status == AnalysisStatus.SUCCESS
    
    print("Testing hiring signal mapping...")
    report = ProjectIntelligenceReport(
        hiring_signal=ProjScoredDimension(
            score=100.0, confidence=1.0
        )
    )
    res = ProjectAnalysisResult(total_projects_count=1, reports=[report])
    result = engine.analyze("t2", res, None, None, None)
    assert result.score_breakdown.project_score == 15.0
    
    print("Testing monotonicity...")
    s1 = SkillProfile(
        skill_name="Python",
        confidence_score=1.0,
        confidence_level="verified",
        evidence_count=5,
        source_count=2,
        skill_depth=DEPTH_ADVANCED,
        hiring_signal="HIGH"
    )
    res_adv = SkillAnalysisResult(total_skills_count=1, skills=[s1])
    result_1 = engine.analyze("t3", None, None, None, res_adv)
    
    s2 = SkillProfile(
        skill_name="HTML",
        confidence_score=0.8,
        confidence_level="likely",
        evidence_count=1,
        source_count=1,
        skill_depth=DEPTH_BEGINNER,
        hiring_signal="LOW"
    )
    res_mixed = SkillAnalysisResult(total_skills_count=2, skills=[s1, s2])
    result_2 = engine.analyze("t3", None, None, None, res_mixed)
    assert result_2.score_breakdown.skill_score > result_1.score_breakdown.skill_score
    
    print("Testing partial status...")
    res = ProjectAnalysisResult(total_projects_count=2, reports=[]) 
    result = engine.analyze("t4", res, None, None, None)
    assert result.analysis_status == AnalysisStatus.PARTIAL
    
    print("Testing serialization...")
    d = result.to_dict()
    assert d["resume_id"] == "t4"
    assert d["analysis_status"] == "PARTIAL"
    assert isinstance(d["score_breakdown"], dict)
    
    print("All tests passed!")

if __name__ == "__main__":
    run_tests()
