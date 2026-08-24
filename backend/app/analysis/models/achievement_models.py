"""
app/analysis/models/achievement_models.py
-----------------------------------------
Awards, honors, and accomplishments domain models for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class AchievementEvidence:
    """
    Represents an award, competition placement, academic honor, or notable accolade.

    Attributes:
        title: Name of the award or honor (e.g. '1st Place in National Hackathon 2025').
        issuer: Granting organization or competition organizer.
        year: Year or timeframe when the achievement was attained.
        description: Details or context explaining the significance of the accomplishment.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    title: str
    issuer: Optional[str] = None
    year: Optional[str] = None
    description: str = ""
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class AchievementAnalysisResult:
    """
    Container for all achievements and awards extracted from a resume.

    Attributes:
        achievements: List of achievement evidence objects.
        total_achievements_count: Total count of achievements identified.
    """
    achievements: List[AchievementEvidence] = field(default_factory=list)
    total_achievements_count: int = 0
