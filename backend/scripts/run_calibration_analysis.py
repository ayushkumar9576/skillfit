import os
import sys
import statistics
import random

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

def generate_sample_profiles(n=40):
    """Generate a realistic distribution of student resumes."""
    profiles = []
    
    # 20% Beginner
    for i in range(int(n * 0.2)):
        profiles.append({
            "tier": "Beginner",
            "name": f"Beginner_Student_{i+1}",
            "projects": [mock_project(f"Portfolio {i}", random.randint(10,25), random.randint(10,25), "prototype", random.randint(5,15), 30)],
            "skills": [mock_skill(f"Skill_{j}", DEPTH_BEGINNER, "LOW") for j in range(3)]
        })
    
    # 50% Intermediate
    for i in range(int(n * 0.5)):
        num_proj = random.choice([1, 2, 2, 3])
        projs = []
        for j in range(num_proj):
            c = random.randint(35, 55)
            projs.append(mock_project(f"CRUD_{i}_{j}", c, c-5, "portfolio", c-10, 50))
        skills = [mock_skill(f"Skill_{j}", DEPTH_INTERMEDIATE, "MEDIUM") for j in range(random.randint(4, 7))]
        profiles.append({
            "tier": "Intermediate",
            "name": f"Intermediate_Student_{i+1}",
            "projects": projs,
            "skills": skills
        })

    # 20% Advanced
    for i in range(int(n * 0.2)):
        num_proj = random.choice([2, 3])
        projs = []
        for j in range(num_proj):
            c = random.randint(65, 80)
            projs.append(mock_project(f"Backend_ML_{i}_{j}", c, c-5, "production_like", c, 75))
        skills = [mock_skill(f"Skill_{j}", DEPTH_ADVANCED, "HIGH") for j in range(random.randint(5, 9))]
        profiles.append({
            "tier": "Advanced",
            "name": f"Advanced_Student_{i+1}",
            "projects": projs,
            "skills": skills
        })

    # 10% High Impact
    for i in range(int(n * 0.1)):
        projs = [
            mock_project(f"MLOps_{i}", random.randint(85, 95), random.randint(85, 95), "industry_level", random.randint(85, 95), 90),
            mock_project(f"Distributed_{i}", random.randint(80, 90), random.randint(80, 90), "industry_level", random.randint(80, 90), 85)
        ]
        skills = [mock_skill(f"Skill_{j}", DEPTH_ADVANCED, "HIGH") for j in range(random.randint(8, 12))]
        profiles.append({
            "tier": "High_Impact",
            "name": f"HighImpact_Student_{i+1}",
            "projects": projs,
            "skills": skills
        })
        
    return profiles


def run_engine_with_weights(engine, p_reports, s_profiles, weights):
    # Temporarily override weights
    original = engine.weights.copy()
    engine.weights = weights
    
    p_res = ProjectAnalysisResult(reports=p_reports, total_projects_count=len(p_reports))
    s_res = SkillAnalysisResult(skills=s_profiles, total_skills_count=len(s_profiles))
    
    result = engine.analyze("test", p_res, None, None, s_res)
    
    engine.weights = original
    return result.readiness_score


if __name__ == "__main__":
    engine = ReadinessEngine()
    
    # -----------------------------------------------------------------
    # AREA 1 & 2: Distribution Analysis on 40 simulated historical profiles
    # -----------------------------------------------------------------
    print("="*60)
    print("AREA 2: SCORE DISTRIBUTION ANALYSIS (N=40)")
    print("="*60)
    
    profiles = generate_sample_profiles(40)
    all_scores = []
    tier_scores = {"Beginner": [], "Intermediate": [], "Advanced": [], "High_Impact": []}
    
    for p in profiles:
        score = run_engine_with_weights(engine, p["projects"], p["skills"], engine.weights)
        all_scores.append(score)
        tier_scores[p["tier"]].append(score)
        
    print(f"Total Profiles: {len(all_scores)}")
    print(f"Minimum Score:  {min(all_scores):.1f}")
    print(f"Maximum Score:  {max(all_scores):.1f}")
    print(f"Mean Score:     {statistics.mean(all_scores):.1f}")
    print(f"Median Score:   {statistics.median(all_scores):.1f}")
    print(f"Std Deviation:  {statistics.stdev(all_scores):.1f}\n")
    
    print("Tier Separation:")
    for tier in ["Beginner", "Intermediate", "Advanced", "High_Impact"]:
        scores = tier_scores[tier]
        if scores:
            print(f"  {tier:<15}: Mean={statistics.mean(scores):.1f}, Min={min(scores):.1f}, Max={max(scores):.1f}")
            
    # -----------------------------------------------------------------
    # AREA 3: Weight Sensitivity
    # -----------------------------------------------------------------
    print("\n" + "="*60)
    print("AREA 3: WEIGHT SENSITIVITY ANALYSIS")
    print("="*60)
    
    variants = {
        "Current": {"projects": 0.45, "skills": 0.30, "internships": 0.15, "certifications": 0.10},
        "Variant A": {"projects": 0.40, "skills": 0.30, "internships": 0.20, "certifications": 0.10},
        "Variant B": {"projects": 0.50, "skills": 0.25, "internships": 0.15, "certifications": 0.10},
        "Variant C": {"projects": 0.45, "skills": 0.25, "internships": 0.20, "certifications": 0.10},
    }
    
    # Select 4 stable test candidates
    test_candidates = [
        {"name": "CRUD", "data": profiles[10]},
        {"name": "ML/Backend", "data": profiles[30]},
        {"name": "MLOps", "data": profiles[-1]},
        {
            "name": "Keyword Inflated", 
            "data": {
                "projects": [mock_project("Todo", 15, 10, "prototype", 5, 40)],
                "skills": [mock_skill(f"S{i}", DEPTH_ADVANCED, "HIGH") for i in range(15)]
            }
        }
    ]
    
    print(f"{'Candidate':<20} | {'Current':<10} | {'Variant A':<10} | {'Variant B':<10} | {'Variant C':<10}")
    print("-" * 75)
    for c in test_candidates:
        row = [f"{c['name']:<20}"]
        for v_name, weights in variants.items():
            s = run_engine_with_weights(engine, c['data']["projects"], c['data']["skills"], weights)
            row.append(f"{s:<10.1f}")
        print(" | ".join(row))

    # -----------------------------------------------------------------
    # AREA 4: Top-End Saturation
    # -----------------------------------------------------------------
    print("\n" + "="*60)
    print("AREA 4: TOP-END SATURATION ANALYSIS")
    print("="*60)
    
    saturation_profiles = {
        "Strong Advanced": {
            "projects": [mock_project("ML Proj", 75, 75, "production_like", 75, 80)],
            "skills": [mock_skill(f"S{i}", DEPTH_ADVANCED, "HIGH") for i in range(8)]
        },
        "High Impact": {
            "projects": [mock_project("MLOps Platform", 90, 90, "industry_level", 90, 90)],
            "skills": [mock_skill(f"S{i}", DEPTH_ADVANCED, "HIGH") for i in range(12)]
        },
        "Exceptional": {
            "projects": [
                mock_project("Cloud Infra (K8s)", 100, 100, "industry_level", 100, 100),
                mock_project("Distributed DB", 95, 95, "industry_level", 100, 100)
            ],
            "skills": [mock_skill(f"S{i}", DEPTH_ADVANCED, "HIGH") for i in range(15)]
        }
    }
    
    for name, data in saturation_profiles.items():
        score = run_engine_with_weights(engine, data["projects"], data["skills"], engine.weights)
        
        p_res = ProjectAnalysisResult(reports=data["projects"], total_projects_count=len(data["projects"]))
        s_res = SkillAnalysisResult(skills=data["skills"], total_skills_count=len(data["skills"]))
        full_res = engine.analyze("test", p_res, None, None, s_res)
        
        print(f"{name:<20}: {score:.1f} (Proj Sub-Score: {full_res.score_breakdown.project_score:.1f}/100)")
