from typing import List, Dict
from app.analysis.models.base import AnalysisEvidence

TECH_PREREQUISITE_GRAPH = {
    "tensorflow": ["python", "machine_learning"],
    "pytorch": ["python", "machine_learning"],
    "keras": ["python", "machine_learning"],
    "django": ["python", "backend_development"],
    "fastapi": ["python", "backend_development", "api_design"],
    "spring": ["java", "backend_development"],
    "react": ["javascript", "frontend_development"],
    "angular": ["javascript", "frontend_development"],
    "node.js": ["javascript", "backend_development"],
}

FOUNDATIONAL_TECH_RELATIONS = TECH_PREREQUISITE_GRAPH

TECHNOLOGY_FAMILY_GRAPH = {
    "tensorflow": ["machine_learning", "deep_learning", "ai_engineering"],
    "pytorch": ["machine_learning", "deep_learning", "ai_engineering"],
    "scikit-learn": ["machine_learning", "data_science"],
    "opencv": ["computer_vision"],
    "django": ["backend_development", "web_development"],
    "fastapi": ["backend_development", "api_design"],
}

def get_derived_competency_contributions(technologies: List[str]) -> Dict[str, float]:
    contributions = {}
    for tech in technologies:
        tech_lower = tech.lower()
        if tech_lower in FOUNDATIONAL_TECH_RELATIONS:
            for competency in FOUNDATIONAL_TECH_RELATIONS[tech_lower]:
                current = contributions.get(competency, 0.0)
                # Diminishing returns formula
                boost = 55.0 * (0.8 ** (current / 55.0))
                contributions[competency] = current + boost
    return contributions

def score_competency(name: str, direct_evidence: List[AnalysisEvidence], derived_contribution: float) -> float:
    from app.analysis.engines.scoring.technology_scoring import score_technology
    
    direct_score = score_technology(direct_evidence, has_results=False)
    
    total_score = direct_score + derived_contribution
    
    return min(100.0, total_score)

def calculate_placement_signals(technologies: List[str]) -> Dict[str, float]:
    signals = {}
    for tech in technologies:
        tech_lower = tech.lower()
        if tech_lower in TECHNOLOGY_FAMILY_GRAPH:
            for family in TECHNOLOGY_FAMILY_GRAPH[tech_lower]:
                current = signals.get(family, 0.0)
                signals[family] = min(1.0, current + 0.35)
    return signals
