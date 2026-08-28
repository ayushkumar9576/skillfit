import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analysis.engines.readiness_engine import ReadinessEngine
from app.analysis.models.project_models import (
    ProjectAnalysisResult,
    ProjectIntelligenceReport,
    ScoredDimension,
    ComplexityAssessment,
    TechnicalMaturity,
)
from app.analysis.models.skill_models import (
    SkillAnalysisResult,
    SkillProfile,
)
from app.analysis.models.readiness_models import DEPTH_ADVANCED, DEPTH_INTERMEDIATE, DEPTH_BEGINNER

def mock_project(title, c_score, d_score, m_class, i_score, h_score):
    report = ProjectIntelligenceReport(project_title=title)
    report.complexity.overall.score = c_score
    report.engineering_depth.score = d_score
    report.technical_maturity.classification = m_class
    report.industry_relevance.score = i_score
    report.hiring_signal.score = h_score
    report.hiring_signal.confidence = 1.0
    report.overall_confidence = 1.0
    return report

def mock_skill(name, depth, signal):
    return SkillProfile(
        skill_name=name,
        skill_depth=depth,
        hiring_signal=signal,
        confidence_score=1.0,
        confidence_level="HIGH",
        evidence_count=1,
        source_count=1
    )

benchmarks = {
    "BEGINNER (Portfolio)": {
        "projects": [
            mock_project("Portfolio", 20, 20, "prototype", 10, 40),
            mock_project("Calculator", 10, 10, "academic", 5, 30),
        ],
        "skills": [
            mock_skill("HTML", DEPTH_BEGINNER, "LOW"),
            mock_skill("CSS", DEPTH_BEGINNER, "LOW"),
        ]
    },
    "INTERMEDIATE (CRUD)": {
        "projects": [
            mock_project("CRUD E-Commerce", 50, 45, "portfolio", 50, 60),
            mock_project("Dashboard", 40, 35, "portfolio", 40, 50),
        ],
        "skills": [
            mock_skill("React", DEPTH_INTERMEDIATE, "MEDIUM"),
            mock_skill("Node.js", DEPTH_INTERMEDIATE, "MEDIUM"),
            mock_skill("PostgreSQL", DEPTH_INTERMEDIATE, "MEDIUM"),
        ]
    },
    "ADVANCED (ML/Backend)": {
        "projects": [
            mock_project("ML Recommendation System", 75, 70, "production_like", 75, 80),
            mock_project("Distributed Backend API", 80, 75, "production_like", 80, 85),
        ],
        "skills": [
            mock_skill("Python", DEPTH_ADVANCED, "HIGH"),
            mock_skill("PyTorch", DEPTH_ADVANCED, "HIGH"),
            mock_skill("Docker", DEPTH_INTERMEDIATE, "MEDIUM"),
        ]
    },
    "HIGH_IMPACT (MLOps)": {
        "projects": [
            mock_project("MLOps Pipeline (ZenML)", 95, 95, "industry_level", 95, 95),
            mock_project("Dynamic OS Scheduler", 90, 85, "industry_level", 85, 90),
        ],
        "skills": [
            mock_skill("Kubernetes", DEPTH_ADVANCED, "HIGH"),
            mock_skill("MLFlow", DEPTH_ADVANCED, "HIGH"),
            mock_skill("ZenML", DEPTH_ADVANCED, "HIGH"),
            mock_skill("Python", DEPTH_ADVANCED, "HIGH"),
        ]
    },
    "KEYWORD_INFLATED": {
        "projects": [
            mock_project("Todo App", 15, 10, "prototype", 5, 40),
            mock_project("Calculator", 10, 10, "academic", 5, 30),
        ],
        "skills": [
            mock_skill("Kubernetes", DEPTH_ADVANCED, "HIGH"),
            mock_skill("Docker", DEPTH_ADVANCED, "HIGH"),
            mock_skill("AWS", DEPTH_ADVANCED, "HIGH"),
            mock_skill("TensorFlow", DEPTH_ADVANCED, "HIGH"),
            mock_skill("Kafka", DEPTH_ADVANCED, "HIGH"),
            mock_skill("Spark", DEPTH_ADVANCED, "HIGH"),
            mock_skill("Python", DEPTH_ADVANCED, "HIGH"),
            mock_skill("React", DEPTH_ADVANCED, "HIGH"),
            mock_skill("Java", DEPTH_ADVANCED, "HIGH"),
            mock_skill("Go", DEPTH_ADVANCED, "HIGH"),
        ]
    }
}

def calculate_old_score(projects, skills):
    # Old logic
    proj_score = 0.0
    for p in projects:
        if p.hiring_signal.score >= 80:
            w = 100.0
        elif p.hiring_signal.score >= 50:
            w = 70.0
        else:
            w = 40.0
        proj_score += 15.0 * (w / 100.0) * p.hiring_signal.confidence
    proj_score = min(proj_score, 100.0)
    
    skill_score = 0.0
    for s in skills:
        depth = (s.skill_depth or "BEGINNER").upper()
        if depth == "ADVANCED":
            val = 15.0
        elif depth == "INTERMEDIATE":
            val = 8.0
        else:
            val = 3.0
            
        is_high = (s.hiring_signal or "LOW").upper() == "HIGH"
        skill_score += val * s.confidence_score * (1.0 if is_high else 0.5)
    skill_score = min(skill_score, 100.0)
    
    # old weights
    return (proj_score * 0.35) + (skill_score * 0.30)

engine = ReadinessEngine()

print("="*75)
print(f"{'PROFILE':<25} | {'OLD READINESS':<15} | {'NEW READINESS':<15}")
print("="*75)

for profile_name, data in benchmarks.items():
    p_res = ProjectAnalysisResult(reports=data["projects"], total_projects_count=len(data["projects"]))
    s_res = SkillAnalysisResult(skills=data["skills"], total_skills_count=len(data["skills"]))
    
    old_score = calculate_old_score(data["projects"], data["skills"])
    new_res = engine.analyze("test-123", p_res, None, None, s_res)
    
    print(f"{profile_name:<25} | {old_score:<15.1f} | {new_res.readiness_score:<15.1f}")

print("\n" + "="*75)
print("EXPLAINABILITY BREAKDOWN FOR KEY PROFILES")
print("="*75)

for profile_name in ["INTERMEDIATE (CRUD)", "HIGH_IMPACT (MLOps)", "KEYWORD_INFLATED"]:
    data = benchmarks[profile_name]
    p_res = ProjectAnalysisResult(reports=data["projects"], total_projects_count=len(data["projects"]))
    s_res = SkillAnalysisResult(skills=data["skills"], total_skills_count=len(data["skills"]))
    new_res = engine.analyze("test-123", p_res, None, None, s_res)
    
    print(f"\n{profile_name}:")
    print(f"  Project Sub-Score:  {new_res.score_breakdown.project_score:.1f}/100")
    print(f"  Skill Sub-Score:    {new_res.score_breakdown.skill_score:.1f}/100")
    print(f"  Project Contributors:")
    for k, v in new_res.score_breakdown.project_contributors.items():
        print(f"    - {k}: {v:.1f}")
