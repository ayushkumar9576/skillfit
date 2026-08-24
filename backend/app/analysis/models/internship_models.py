"""
app/analysis/models/internship_models.py
----------------------------------------
Internship analysis domain models for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.8: Internship Analysis Engine
    - Phase 3.10: Evidence-Based Skill Engine
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class InternshipEvidence:
    """
    Represents an internship experience extracted from resume content.

    Attributes:
        organization: Company or institution name.
        role: Internship title (e.g. 'Software Engineer Intern', 'Data Science Intern').
        duration: Date range or timeframe of the internship.
        location: Geographic location or 'Remote'.
        description: Summary of work and core responsibilities.
        technologies_used: List of technical tools and frameworks applied.
        achievements: Quantifiable outcomes or key deliverables accomplished.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    organization: str
    role: str
    duration: Optional[str] = None
    location: Optional[str] = None
    description: str = ""
    technologies_used: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class InternshipAnalysisResult:
    """
    Container for all internship experiences extracted from a resume.

    Attributes:
        internships: List of extracted internship evidence objects.
        total_internships_count: Total count of internships identified.
    """
    internships: List[InternshipEvidence] = field(default_factory=list)
    total_internships_count: int = 0
