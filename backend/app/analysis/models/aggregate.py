"""
app/analysis/models/aggregate.py
--------------------------------
Root aggregate container and candidate contact structures for SkillFit
Analysis Domain Model Layer (Phase 3.5).

Provides:
    - CandidateContact: Structured contact information and profile URLs.
    - ResumeAnalysis: Root aggregate holding all domain analysis results.

Design Rules:
    - Pure standard library dataclasses only.
    - Progressive population support (all sub-results default to None).
    - Open extension mechanism via 'extensions' dictionary.
    - Seamless serialization to nested dictionaries via dataclasses.asdict().
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.analysis.models.achievement_models import AchievementAnalysisResult
from app.analysis.models.base import AnalysisEvidence, AnalysisMetadata
from app.analysis.models.certification_models import CertificationAnalysisResult
from app.analysis.models.education_models import EducationAnalysisResult
from app.analysis.models.experience_models import ExperienceAnalysisResult
from app.analysis.models.internship_models import InternshipAnalysisResult
from app.analysis.models.leadership_models import (
    PositionOfResponsibilityAnalysisResult,
)
from app.analysis.models.project_models import ProjectAnalysisResult
from app.analysis.models.publication_models import PublicationAnalysisResult
from app.analysis.models.readiness_models import ReadinessAnalysisResult
from app.analysis.models.skill_models import SkillAnalysisResult


@dataclass
class CandidateContact:
    """
    Structured contact and identity information extracted from the candidate's resume.

    Attributes:
        full_name: Extracted candidate name.
        email: Contact email address.
        phone: Contact phone number.
        linkedin_url: LinkedIn profile URL if identified.
        github_url: GitHub profile URL if identified.
        portfolio_url: Personal portfolio or website URL if identified.
        location: City, state, or country of residence if identified.
        evidences: List of supporting resume textual statements.
    """
    full_name: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    location: Optional[str] = None
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class ResumeAnalysis:
    """
    The canonical Root Aggregate containing the complete analytical breakdown
    of a resume across all intelligence dimensions.

    Progressive Population Lifecycle:
        1. Instantiated with `metadata` when analysis commences.
        2. Phase 3.7 populates `projects`.
        3. Phase 3.8 populates `internships` and `experience`.
        4. Phase 3.9 populates `certifications`.
        5. Phase 3.10 populates `skills` with verified cross-section evidence.
        6. Phase 3.11 consumes all populated facets and sets `readiness`.
        7. Phase 3.12 persists this aggregate to the relational/JSONB database.
        8. Phase 3.13 serializes this aggregate to Pydantic v2 schemas for the public API.

    Attributes:
        metadata: Analysis execution metadata (resume ID, version, timestamp, engine).
        contact: Extracted candidate contact details and portfolio links.
        skills: Verified technical and domain skills analysis result.
        projects: Extracted technical projects analysis result.
        internships: Extracted internships analysis result.
        experience: Extracted professional work experience analysis result.
        education: Academic background and qualifications analysis result.
        certifications: Verified certifications and licenses analysis result.
        achievements: Extracted honors, awards, and accolades analysis result.
        positions_of_responsibility: Leadership and extracurricular roles analysis result.
        publications: Research papers, publications, and patents analysis result.
        readiness: Composite readiness scoring and placement recommendation result.
        extensions: Open dictionary for future specialized engine payloads (e.g. ATS score, GitHub repo metrics).
    """
    metadata: AnalysisMetadata
    contact: Optional[CandidateContact] = None
    skills: Optional[SkillAnalysisResult] = None
    projects: Optional[ProjectAnalysisResult] = None
    internships: Optional[InternshipAnalysisResult] = None
    experience: Optional[ExperienceAnalysisResult] = None
    education: Optional[EducationAnalysisResult] = None
    certifications: Optional[CertificationAnalysisResult] = None
    achievements: Optional[AchievementAnalysisResult] = None
    positions_of_responsibility: Optional[PositionOfResponsibilityAnalysisResult] = None
    publications: Optional[PublicationAnalysisResult] = None
    readiness: Optional[ReadinessAnalysisResult] = None
    extensions: Dict[str, Any] = field(default_factory=dict)
