"""
app/analysis/models
-------------------
Submodule re-exports for SkillFit Phase 3.5 Analysis Domain Models.
"""

from app.analysis.models.base import (
    AnalysisEvidence,
    AnalysisMetadata,
)
from app.analysis.models.skill_models import (
    SkillEvidence,
    SkillAnalysisResult,
)
from app.analysis.models.project_models import (
    ProjectEvidence,
    ProjectAnalysisResult,
)
from app.analysis.models.internship_models import (
    InternshipEvidence,
    InternshipAnalysisResult,
)
from app.analysis.models.experience_models import (
    ExperienceEvidence,
    ExperienceAnalysisResult,
)
from app.analysis.models.education_models import (
    EducationEvidence,
    EducationAnalysisResult,
)
from app.analysis.models.certification_models import (
    CertificationEvidence,
    CertificationAnalysisResult,
)
from app.analysis.models.achievement_models import (
    AchievementEvidence,
    AchievementAnalysisResult,
)
from app.analysis.models.leadership_models import (
    PositionOfResponsibilityEvidence,
    PositionOfResponsibilityAnalysisResult,
)
from app.analysis.models.publication_models import (
    PublicationEvidence,
    PublicationAnalysisResult,
)
from app.analysis.models.readiness_models import (
    CategoryScore,
    ReadinessAnalysisResult,
)
from app.analysis.models.aggregate import (
    CandidateContact,
    ResumeAnalysis,
)

__all__ = [
    # Base Primitives
    "AnalysisEvidence",
    "AnalysisMetadata",
    # Aggregate & Identity
    "CandidateContact",
    "ResumeAnalysis",
    # Skill Domain
    "SkillEvidence",
    "SkillAnalysisResult",
    # Project Domain
    "ProjectEvidence",
    "ProjectAnalysisResult",
    # Internship Domain
    "InternshipEvidence",
    "InternshipAnalysisResult",
    # Experience Domain
    "ExperienceEvidence",
    "ExperienceAnalysisResult",
    # Education Domain
    "EducationEvidence",
    "EducationAnalysisResult",
    # Certification Domain
    "CertificationEvidence",
    "CertificationAnalysisResult",
    # Achievement Domain
    "AchievementEvidence",
    "AchievementAnalysisResult",
    # Leadership Domain
    "PositionOfResponsibilityEvidence",
    "PositionOfResponsibilityAnalysisResult",
    # Publication Domain
    "PublicationEvidence",
    "PublicationAnalysisResult",
    # Readiness Domain
    "CategoryScore",
    "ReadinessAnalysisResult",
]
