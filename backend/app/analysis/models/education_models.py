"""
app/analysis/models/education_models.py
---------------------------------------
Academic education and qualification domain models for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class EducationEvidence:
    """
    Represents an academic degree, diploma, or educational qualification.

    Attributes:
        institution: College, university, or school name.
        degree: Degree type (e.g. 'B.Tech', 'M.S.', 'Bachelor of Science').
        field_of_study: Major or specialization (e.g. 'Computer Science & Engineering').
        duration: Years or date range of study (e.g. '2022 - 2026').
        grade_type: Grading standard ('CGPA', 'Percentage', 'GPA').
        grade_value: Reported grade or score (e.g. '8.9 / 10.0', '85%').
        coursework: Relevant academic courses or focus areas.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    duration: Optional[str] = None
    grade_type: Optional[str] = None
    grade_value: Optional[str] = None
    coursework: List[str] = field(default_factory=list)
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class EducationAnalysisResult:
    """
    Container for all academic qualifications extracted from a resume.

    Attributes:
        education_entries: List of academic degree evidence objects.
        highest_degree: Normalized highest degree identified.
    """
    education_entries: List[EducationEvidence] = field(default_factory=list)
    highest_degree: Optional[str] = None
