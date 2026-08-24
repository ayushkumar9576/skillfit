"""
app/analysis/models/experience_models.py
----------------------------------------
Work and professional experience domain models for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.10: Evidence-Based Skill Engine
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class ExperienceEvidence:
    """
    Represents a full-time, part-time, or contract professional work experience.

    Attributes:
        organization: Company or employer name.
        role: Job title (e.g. 'Junior Backend Developer', 'Associate Consultant').
        duration: Date range or employment timeframe.
        location: Work location or 'Remote'.
        description: Description of core job functions and responsibilities.
        is_current: Boolean indicating if this is candidate's active role.
        achievements: Quantifiable bullet points or milestones.
        technologies_used: Technologies, tools, or methodologies applied.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    organization: str
    role: str
    duration: Optional[str] = None
    location: Optional[str] = None
    description: str = ""
    is_current: bool = False
    achievements: List[str] = field(default_factory=list)
    technologies_used: List[str] = field(default_factory=list)
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class ExperienceAnalysisResult:
    """
    Container for all professional work experience entries extracted from a resume.

    Attributes:
        experiences: List of work experience evidence objects.
        total_experience_count: Total count of job entries identified.
    """
    experiences: List[ExperienceEvidence] = field(default_factory=list)
    total_experience_count: int = 0
