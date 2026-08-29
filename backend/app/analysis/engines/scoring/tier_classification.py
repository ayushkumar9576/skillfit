from typing import List
from app.analysis.models.base import AnalysisEvidence

def calculate_technical_maturity(
    architecture_ev: List[AnalysisEvidence],
    deployment_ev: List[AnalysisEvidence],
    testing_ev: List[AnalysisEvidence],
    security_ev: List[AnalysisEvidence],
    monitoring_ev: List[AnalysisEvidence],
    integration_ev: List[AnalysisEvidence]
) -> float:
    score = 0.0
    
    if any(getattr(e, 'validated', True) for e in architecture_ev):
        score += 25.0
    if any(getattr(e, 'validated', True) for e in deployment_ev):
        score += 15.0
    if any(getattr(e, 'validated', True) for e in testing_ev):
        score += 15.0
    if any(getattr(e, 'validated', True) for e in security_ev):
        score += 15.0
    if any(getattr(e, 'validated', True) for e in monitoring_ev):
        score += 10.0
    if any(getattr(e, 'validated', True) for e in integration_ev):
        score += 20.0
        
    return min(100.0, score)

def classify_project_tier(maturity_score: float, complexity_score: float, business_impact_score: float) -> str:
    if business_impact_score == 0.0:
        # Normalize using only maturity and complexity (50/35 ratio => 50/85 and 35/85)
        # Or just 60/40 approx
        tier_score = (maturity_score * 0.588) + (complexity_score * 0.412)
    else:
        tier_score = (maturity_score * 0.50) + (complexity_score * 0.35) + (business_impact_score * 0.15)
        
    if tier_score <= 25:
        return "TOY"
    elif tier_score <= 50:
        return "PORTFOLIO"
    elif tier_score <= 75:
        return "PRODUCTION_LIKE"
    else:
        return "INDUSTRY_GRADE"
