import os
import sys
import json

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.analysis.engines.readiness_engine import ReadinessEngine
from app.analysis.models.project_models import (
    ProjectAnalysisResult,
    ProjectIntelligenceReport,
)
from app.analysis.models.skill_models import (
    SkillAnalysisResult,
    SkillProfile,
)

def calculate_old_score(projects, skills):
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
    
    return (proj_score * 0.35) + (skill_score * 0.30)

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


if __name__ == "__main__":
    engine = ReadinessEngine()
    
    print("="*75)
    print("1. ACTUAL ANALYZED RESUME (From DEBUG JSON)")
    print("="*75)
    
    try:
        with open("DEBUG/results/debug_project.json", "r") as f:
            p_data = json.load(f)
            
        reports = []
        for r_data in p_data.get("reports", []):
            comp_data = r_data.get("complexity", {})
            overall = comp_data.get("overall", {})
            c_score = overall.get("score", 0.0)
            d_score = r_data.get("engineering_depth", {}).get("score", 0.0)
            m_class = r_data.get("technical_maturity", {}).get("classification", "")
            i_score = r_data.get("industry_relevance", {}).get("score", 0.0)
            h_score = r_data.get("hiring_signal", {}).get("score", 0.0)
            title = r_data.get("project_title", "")
            reports.append(mock_project(title, c_score, d_score, m_class, i_score, h_score))
            
        p_res = ProjectAnalysisResult(reports=reports, total_projects_count=len(reports))
        
        with open("DEBUG/results/debug_skill.json", "r") as f:
            s_data = json.load(f)
            
        skills = []
        for s in s_data.get("skills", []):
            skills.append(mock_skill(s.get("skill_name", ""), s.get("skill_depth", ""), s.get("hiring_signal", "")))
            
        s_res = SkillAnalysisResult(skills=skills, total_skills_count=len(skills))
            
        old_score = calculate_old_score(p_res.reports, s_res.skills)
        new_res = engine.analyze("test-actual", p_res, None, None, s_res)
        
        print(f"Candidate B (ML/MLOps Portfolio)")
        print(f"  Old Score: {old_score:.1f}")
        print(f"  New Score: {new_res.readiness_score:.1f}")
        print(f"  Project Contributors:")
        for k, v in new_res.score_breakdown.project_contributors.items():
            print(f"    - {k}: {v:.1f}")
            
    except Exception as e:
        print(f"Error loading debug JSONs: {e}")
        
    print("\n" + "="*75)
    print("2. TOP-END DIFFERENTIATION TEST")
    print("="*75)
    
    top_end_profiles = {
        "Strong MLOps": {
            "projects": [
                mock_project("End-to-End MLOps Pipeline (ZenML/MLFlow)", 95, 95, "industry_level", 95, 95),
                mock_project("Real-time Inference Engine", 90, 85, "production_like", 90, 90)
            ],
            "skills": [mock_skill(f"S{i}", "ADVANCED", "HIGH") for i in range(10)]
        },
        "Exceptional Engineering": {
            "projects": [
                mock_project("Distributed Kubernetes Cloud Infra", 100, 100, "industry_level", 100, 100),
                mock_project("Low-Latency Microservices Architecture", 95, 95, "industry_level", 95, 95)
            ],
            "skills": [mock_skill(f"S{i}", "ADVANCED", "HIGH") for i in range(15)]
        }
    }
    
    for name, data in top_end_profiles.items():
        old_s = calculate_old_score(data["projects"], data["skills"])
        
        p_res = ProjectAnalysisResult(reports=data["projects"], total_projects_count=len(data["projects"]))
        s_res = SkillAnalysisResult(skills=data["skills"], total_skills_count=len(data["skills"]))
        new_res = engine.analyze("test", p_res, None, None, s_res)
        
        print(f"{name}")
        print(f"  Old Score: {old_s:.1f}")
        print(f"  New Score: {new_res.readiness_score:.1f} (Proj Sub-Score: {new_res.score_breakdown.project_score:.1f}/100)")
