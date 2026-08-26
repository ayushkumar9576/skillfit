"""
app/analysis
------------
SkillFit AI & Placement Intelligence Analysis Domain.

Provides canonical domain contracts for:
    - Phase 3.5: Analysis Domain Models
    - Future Phase 3.6: LLM Integration Layer
    - Future Phase 3.7: Project Analysis Engine
    - Future Phase 3.8: Internship Analysis Engine
    - Future Phase 3.9: Certification Analysis Engine
    - Future Phase 3.10: Evidence-Based Skill Engine
    - Future Phase 3.11: Readiness Engine
    - Future Phase 3.12: Analysis Persistence
    - Future Phase 3.13: Public CV APIs
"""

from app.analysis.models import (
    AchievementAnalysisResult,
    AchievementEvidence,
    AnalysisEvidence,
    AnalysisMetadata,
    ArchitectureFacet,
    AssessedPoint,
    CANNOT_VERIFY,
    CandidateContact,
    CategoryScore,
    CertificationAnalysisResult,
    CertificationEvidence,
    Competency,
    ComplexityAssessment,
    EducationAnalysisResult,
    EducationEvidence,
    ExecutiveAssessment,
    ExperienceAnalysisResult,
    ExperienceEvidence,
    InternshipAnalysisResult,
    InternshipEvidence,
    MissingEvidenceItem,
    PositionOfResponsibilityAnalysisResult,
    PositionOfResponsibilityEvidence,
    ProjectAnalysisResult,
    ProjectEvidence,
    ProjectIntelligenceReport,
    ProjectUnderstanding,
    PublicationAnalysisResult,
    PublicationEvidence,
    ReadinessAnalysisResult,
    ResumeAnalysis,
    ScoredDimension,
    SkillAnalysisResult,
    SkillEvidence,
    SkillEvidenceItem,
    SkillEvidenceMap,
    TechnicalMaturity,
    TechnologyUsage,
)

__all__ = [
    # Primary Root Aggregate
    "ResumeAnalysis",
    "CandidateContact",
    # Metadata & Evidence Primitives
    "AnalysisMetadata",
    "AnalysisEvidence",
    # Domain Results & Evidence
    "SkillEvidence",
    "SkillAnalysisResult",
    "ProjectEvidence",
    "ProjectAnalysisResult",
    # Project Intelligence (Phase 3.7)
    "CANNOT_VERIFY",
    "ScoredDimension",
    "ProjectUnderstanding",
    "ArchitectureFacet",
    "ComplexityAssessment",
    "TechnologyUsage",
    "Competency",
    "SkillEvidenceItem",
    "SkillEvidenceMap",
    "TechnicalMaturity",
    "AssessedPoint",
    "MissingEvidenceItem",
    "ExecutiveAssessment",
    "ProjectIntelligenceReport",
    "InternshipEvidence",
    "InternshipAnalysisResult",
    "ExperienceEvidence",
    "ExperienceAnalysisResult",
    "EducationEvidence",
    "EducationAnalysisResult",
    "CertificationEvidence",
    "CertificationAnalysisResult",
    "AchievementEvidence",
    "AchievementAnalysisResult",
    "PositionOfResponsibilityEvidence",
    "PositionOfResponsibilityAnalysisResult",
    "PublicationEvidence",
    "PublicationAnalysisResult",
    "CategoryScore",
    "ReadinessAnalysisResult",
]
