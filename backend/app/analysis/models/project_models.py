"""
app/analysis/models/project_models.py
-------------------------------------
Project analysis domain models for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.7: Project Analysis Engine
    - Phase 3.10: Evidence-Based Skill Engine
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class ProjectEvidence:
    """
    Represents an extracted project artifact from resume text.

    Attributes:
        title: Project name or title.
        description: Comprehensive summary of the project.
        role: Candidate's role in the project (e.g. 'Sole Developer', 'Backend Lead').
        technologies: List of technologies, languages, and tools utilized.
        project_url: Repository or live deployment URL if available.
        highlights: Key quantifiable bullet points or achievements from the project.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting textual statements.
    """
    title: str
    description: str = ""
    role: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    project_url: Optional[str] = None
    highlights: List[str] = field(default_factory=list)
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class ProjectAnalysisResult:
    """
    Container for all project findings extracted from a resume.

    Attributes:
        projects: List of extracted project evidence objects.
        total_projects_count: Total number of valid projects identified.
    """
    projects: List[ProjectEvidence] = field(default_factory=list)
    total_projects_count: int = 0
