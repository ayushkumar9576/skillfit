"""
app/analysis/utils/scoring.py
-----------------------------
Shared capability scoring utilities for SkillFit Phase 3.12.
Ensures One Capability Language across Readiness, Domain Aggregation, and Phase 5.
"""

from typing import Dict, Any

def calculate_project_capability_score(report: Any) -> Dict[str, float]:
    """
    Calculates the canonical Project Capability Score for a given ProjectIntelligenceReport.
    
    Returns a dictionary with raw scores and the final capability score,
    ensuring deterministic, duplicated-free scoring across the platform.
    """
    maturity_scores = {
        "prototype": 20.0,
        "academic": 40.0,
        "portfolio": 60.0,
        "production_like": 80.0,
        "industry_level": 100.0,
    }

    # Extract dimensions
    c_score = getattr(report.complexity.overall, "score", 0.0) if hasattr(report, "complexity") and hasattr(report.complexity, "overall") else 0.0
    d_score = getattr(report.engineering_depth, "score", 0.0) if hasattr(report, "engineering_depth") else 0.0
    i_score = getattr(report.industry_relevance, "score", 0.0) if hasattr(report, "industry_relevance") else 0.0
    
    maturity_class = getattr(report.technical_maturity, "classification", "") if hasattr(report, "technical_maturity") else ""
    m_score = maturity_scores.get(maturity_class.lower(), 20.0)

    # Calculate base capability (the canonical capability language)
    # Weights calibrated in Phase 3.11
    base_capability = (c_score * 0.30) + (d_score * 0.30) + (m_score * 0.25) + (i_score * 0.15)
    
    # Get extraction confidence
    conf = report.overall_confidence if getattr(report, "overall_confidence", 0.0) > 0 else 1.0
    conf = max(0.0, min(conf, 1.0))

    return {
        "c_score": c_score,
        "d_score": d_score,
        "m_score": m_score,
        "i_score": i_score,
        "base_capability": base_capability,
        "confidence": conf,
        "final_capability_score": base_capability * conf
    }
