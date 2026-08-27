"""
app/schemas/resume_analysis.py
-------------------------------
Pydantic v2 response schemas for the Phase 3.13 CV Analysis API layer.

Design rules:
    - Never expose ORM models directly.
    - Exclude all internal fields: file_path, file_hash, extracted_text,
      raw student_id integers, internal DB row IDs.
    - contact section is always stripped from section responses (PII).
    - All schemas use from_attributes=True for ORM compatibility.
"""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    ConfidenceLevel,
    ComplexityLabel,
    ExperienceStrengthLabel,
    ProcessingStatus,
    ReadinessLevel,
    ResumeType,
    TechnicalDepthLabel,
)


# ---------------------------------------------------------------------------
# Queue / Admin schemas
# ---------------------------------------------------------------------------


class PendingResumeItem(BaseModel):
    """One entry in the admin pending-queue list."""
    model_config = ConfigDict(from_attributes=True)

    resume_id: uuid.UUID
    student_id: int
    student_name: str
    resume_type: ResumeType
    processing_status: ProcessingStatus
    upload_date: datetime


class PendingQueueResponse(BaseModel):
    """Response for GET /api/v1/admin/resumes/pending."""
    items: List[PendingResumeItem]
    total: int


class QueueSummaryResponse(BaseModel):
    """Response for GET /api/v1/admin/resumes/queue-summary."""
    uploaded: int
    processing: int
    completed: int
    failed: int


class AdminResumeStatusResponse(BaseModel):
    """Response for GET /api/v1/admin/resumes/{resume_id}/status."""
    resume_id: uuid.UUID
    student_id: int
    resume_type: ResumeType
    processing_status: ProcessingStatus
    analysis_status: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    last_updated: datetime


class AnalyzeTriggerResponse(BaseModel):
    """Response for POST /api/v1/admin/resumes/{resume_id}/analyze."""
    resume_id: uuid.UUID
    status: str = "queued"
    message: str


class BatchAnalyzeRequest(BaseModel):
    """Request body for POST /api/v1/admin/resumes/analyze-batch."""
    resume_ids: Optional[List[uuid.UUID]] = Field(
        default=None,
        description="Explicit list of resume UUIDs to process. If omitted, `limit` is required.",
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Max number of pending/failed resumes to process. Required if resume_ids is not provided.",
    )


class BatchAnalyzeResponse(BaseModel):
    """Response for POST /api/v1/admin/resumes/analyze-batch."""
    queued: List[uuid.UUID]
    skipped: List[uuid.UUID]
    reasons: Dict[str, str]
    total_queued: int
    total_skipped: int


# ---------------------------------------------------------------------------
# Readiness schema
# ---------------------------------------------------------------------------


class ReadinessResponse(BaseModel):
    """Response for GET /api/v1/resumes/{resume_id}/readiness."""
    model_config = ConfigDict(from_attributes=True)

    resume_id: uuid.UUID
    readiness_level: Optional[ReadinessLevel]
    readiness_explanation: Optional[str]
    summary: Optional[str]
    strengths: Optional[Dict[str, Any]]
    weaknesses: Optional[Dict[str, Any]]
    analyzed_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Skills schema
# ---------------------------------------------------------------------------


class SkillResponse(BaseModel):
    """A single skill profile returned to the student."""
    model_config = ConfigDict(from_attributes=True)

    skill_name: str
    confidence_score: Optional[int]
    confidence_level: Optional[ConfidenceLevel]
    evidence_sources: Optional[Dict[str, Any]]


class SkillsListResponse(BaseModel):
    """Response for GET /api/v1/resumes/{resume_id}/skills."""
    resume_id: uuid.UUID
    skills: List[SkillResponse]
    total: int


# ---------------------------------------------------------------------------
# Projects schema
# ---------------------------------------------------------------------------


class ProjectResponse(BaseModel):
    """A single project record returned to the student."""
    model_config = ConfigDict(from_attributes=True)

    project_name: str
    domain: Optional[str]
    description: str
    tech_stack: str
    complexity_score: Optional[int]
    complexity_label: Optional[ComplexityLabel]
    technical_depth_score: Optional[int]
    technical_depth_label: Optional[TechnicalDepthLabel]
    github_url: Optional[str]


class ProjectsListResponse(BaseModel):
    """Response for GET /api/v1/resumes/{resume_id}/projects."""
    resume_id: uuid.UUID
    projects: List[ProjectResponse]
    total: int


# ---------------------------------------------------------------------------
# Internships schema
# ---------------------------------------------------------------------------


class InternshipResponse(BaseModel):
    """A single internship record returned to the student."""
    model_config = ConfigDict(from_attributes=True)

    company_name: str
    role: str
    description: Optional[str]
    industry: Optional[str]
    technologies_used: Optional[Dict[str, Any]]
    experience_strength_score: Optional[int]
    experience_strength_label: Optional[ExperienceStrengthLabel]


class InternshipsListResponse(BaseModel):
    """Response for GET /api/v1/resumes/{resume_id}/internships."""
    resume_id: uuid.UUID
    internships: List[InternshipResponse]
    total: int


# ---------------------------------------------------------------------------
# Certifications schema
# ---------------------------------------------------------------------------


class CertificationResponse(BaseModel):
    """A single certification record returned to the student."""
    model_config = ConfigDict(from_attributes=True)

    name: str
    issuer: str
    issue_date: Optional[date]
    credential_url: Optional[str]
    technical_depth_score: Optional[int]
    industry_relevance: Optional[str]
    industry_value: Optional[int]


class CertificationsListResponse(BaseModel):
    """Response for GET /api/v1/resumes/{resume_id}/certifications."""
    resume_id: uuid.UUID
    certifications: List[CertificationResponse]
    total: int


# ---------------------------------------------------------------------------
# Sections schema
# ---------------------------------------------------------------------------

# All canonical section keys the section detector produces.
# "contact" is intentionally excluded — it contains PII.
_SAFE_SECTION_KEYS = {
    "education",
    "skills",
    "projects",
    "internships",
    "certifications",
    "achievements",
    "publications",
    "positions_of_responsibility",
    "summary",
    "experience",
    "other",
}


class SectionsResponse(BaseModel):
    """
    Response for GET /api/v1/resumes/{resume_id}/sections.

    The `contact` section is always stripped before return.
    `contact_present` indicates whether contact info was detected,
    without exposing the raw phone/email/address values.
    """
    resume_id: uuid.UUID
    contact_present: bool
    sections: Dict[str, Any]
