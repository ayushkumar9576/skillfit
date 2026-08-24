"""
app/analysis/models/readiness_models.py
---------------------------------------
Composite readiness, evaluation scoring, and placement readiness domain models
for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class CategoryScore:
    """
    Sub-score for a specific competency dimension evaluated by the Readiness Engine.

    Attributes:
        category_name: Name of evaluated facet (e.g. 'Skills', 'Projects', 'Experience', 'Education').
        score: Computed numerical score (e.g. 0.0 to 100.0).
        max_score: Maximum attainable score (default 100.0).
        weight: Weight of this category in the composite readiness score.
        feedback: Specific feedback on this category.
    """
    category_name: str
    score: float = 0.0
    max_score: float = 100.0
    weight: float = 1.0
    feedback: Optional[str] = None


@dataclass
class ReadinessAnalysisResult:
    """
    Composite evaluation result produced by the Phase 3.11 Readiness Engine.

    Attributes:
        overall_score: Composite placement readiness score (0.0 to 100.0).
        readiness_level: Standardized readiness tier ('beginner', 'intermediate', 'advanced', 'industry_ready').
        summary: High-level narrative summary of candidate strengths and profile readiness.
        category_scores: Detailed breakdown across individual evaluation dimensions.
        strengths: Key identified competitive advantages of the candidate.
        weaknesses: Core areas of improvement or missing elements.
        recommendations: Actionable placement preparation recommendations.
        key_risks: Potential gaps or recruiter concerns identified in the profile.
        evidences: List of supporting cross-section evidence statements.
    """
    overall_score: float = 0.0
    readiness_level: str = "beginner"
    summary: str = ""
    category_scores: Dict[str, CategoryScore] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    evidences: List[AnalysisEvidence] = field(default_factory=list)
