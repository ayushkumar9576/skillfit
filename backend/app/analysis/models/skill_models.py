"""
app/analysis/models/skill_models.py
-----------------------------------
Skill analysis domain models for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.10: Evidence-Based Skill Engine
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class SkillEvidence:
    """
    Represents an identified skill along with verified evidence and category metadata.

    Attributes:
        skill_name: Name of the technical or domain skill (e.g. 'Python', 'FastAPI', 'Docker').
        category: Skill classification (e.g. 'Programming Languages', 'Frameworks', 'Databases', 'Cloud').
        proficiency_level: Verified proficiency estimation (e.g. 'beginner', 'intermediate', 'advanced').
        confidence: Confidence score of the extraction / verification (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    skill_name: str
    category: str = "General"
    proficiency_level: Optional[str] = None
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class SkillAnalysisResult:
    """
    Container for all skill analysis findings across a resume.

    Attributes:
        skills: List of verified skill evidence objects.
        total_skills_count: Total count of unique skills identified.
        categories_breakdown: Breakdown mapping category name to count of skills.
    """
    skills: List[SkillEvidence] = field(default_factory=list)
    total_skills_count: int = 0
    categories_breakdown: Dict[str, int] = field(default_factory=dict)
