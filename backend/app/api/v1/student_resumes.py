"""
app/api/v1/student_resumes.py
------------------------------
Phase 3.13 Student CV Analysis API — all endpoints under /api/v1/resumes.

Endpoints:
    POST   /api/v1/resumes                           — Upload resume (no pipeline trigger)
    GET    /api/v1/resumes                           — List own resumes
    GET    /api/v1/resumes/{resume_id}               — Get single resume metadata
    DELETE /api/v1/resumes/{resume_id}               — Delete resume (409 if processing)
    GET    /api/v1/resumes/{resume_id}/readiness     — Readiness score (completed only)
    GET    /api/v1/resumes/{resume_id}/skills        — Skills (completed only)
    GET    /api/v1/resumes/{resume_id}/projects      — Projects (completed only)
    GET    /api/v1/resumes/{resume_id}/internships   — Internships (completed only)
    GET    /api/v1/resumes/{resume_id}/certifications — Certifications (completed only)
    GET    /api/v1/resumes/{resume_id}/sections      — Sections, contact stripped (completed only)

Security:
    - All endpoints require UserRole.student via require_roles().
    - Ownership is enforced: resume.student_id must equal current student.id.
      Violations return 404 (not 403) to prevent IDOR enumeration.
    - Analysis endpoints return 404 with "Analysis not yet available." when
      processing_status != completed — never leak internal state.
    - contact section is always removed from sections response.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.enums import ProcessingStatus, ResumeType, UserRole
from app.models.certification import Certification
from app.models.cv_analysis import CVAnalysis
from app.models.resume_file import ResumeFile
from app.models.student import Student
from app.models.student_internship import StudentInternship
from app.models.student_project import StudentProject
from app.models.student_skill import StudentSkill
from app.models.user import User
from app.schemas.resume import ResumeListResponse, ResumeResponse
from app.schemas.resume_analysis import (
    CertificationResponse,
    CertificationsListResponse,
    InternshipResponse,
    InternshipsListResponse,
    ProjectResponse,
    ProjectsListResponse,
    ReadinessResponse,
    SectionsResponse,
    SkillResponse,
    SkillsListResponse,
    _SAFE_SECTION_KEYS,
)
from app.services import resume_service
from fastapi import HTTPException

router = APIRouter(prefix="/api/v1/resumes", tags=["Student — Resume & Analysis"])


# ---------------------------------------------------------------------------
# Internal security helpers
# ---------------------------------------------------------------------------


def _get_student(db: Session, user: User) -> Student:
    """Resolve the Student profile for this User. Returns 403 if not found."""
    student: Student | None = (
        db.query(Student).filter(Student.user_id == user.id).first()
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to student accounts.",
        )
    return student


def _get_owned_resume(db: Session, resume_id: uuid.UUID, student_id: int) -> ResumeFile:
    """
    Load a resume by ID and verify ownership.

    Returns 404 regardless of whether the record doesn't exist or belongs to
    another student — this prevents IDOR enumeration attacks.
    """
    resume: ResumeFile | None = (
        db.query(ResumeFile).filter(ResumeFile.id == resume_id).first()
    )
    if resume is None or resume.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )
    return resume


def _require_completed(resume: ResumeFile) -> None:
    """Raise 404 if analysis is not yet complete. Never expose internal status."""
    if resume.processing_status != ProcessingStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not yet available.",
        )


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume",
    description=(
        "Upload a PDF or DOCX resume file with a specified type. "
        "Analysis is NOT triggered automatically — an Admin must trigger it via "
        "POST /api/v1/admin/resumes/{id}/analyze. "
        "Returns immediately after file validation and storage."
    ),
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (.pdf or .docx, max 10 MB)."),
    resume_type: ResumeType = Form(..., description="'generic' or 'specialized'."),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ResumeResponse:
    return await resume_service.upload_resume(
        db, file, current_user.id, resume_type
    )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ResumeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List own resumes",
    description="Returns all resumes uploaded by the authenticated student, newest first.",
)
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ResumeListResponse:
    return resume_service.list_resumes(db, current_user.id)


# ---------------------------------------------------------------------------
# Get single resume
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single resume",
    description=(
        "Returns metadata for one resume including processing_status. "
        "Ownership strictly enforced."
    ),
)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ResumeResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    return ResumeResponse.model_validate(resume)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume",
    description=(
        "Permanently deletes a resume and its analysis data. "
        "Returns 409 Conflict if analysis is currently running."
    ),
)
def delete_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> None:
    resume_service.delete_resume(db, resume_id, current_user.id)


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/readiness",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get readiness analysis",
    description="Returns AI-generated readiness score. Only available after analysis completes.",
)
def get_readiness(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ReadinessResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    cv: CVAnalysis | None = (
        db.query(CVAnalysis).filter(CVAnalysis.resume_id == resume_id).first()
    )
    if cv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not yet available.",
        )

    return ReadinessResponse(
        resume_id=resume_id,
        readiness_level=cv.readiness_level,
        readiness_explanation=cv.readiness_explanation,
        summary=cv.summary,
        strengths=cv.strengths,
        weaknesses=cv.weaknesses,
        analyzed_at=cv.analyzed_at,
    )


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/skills",
    response_model=SkillsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get skill profiles",
    description="Returns evidence-based skill assessments. Only available after analysis completes.",
)
def get_skills(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> SkillsListResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    skills = (
        db.query(StudentSkill)
        .filter(StudentSkill.resume_id == resume_id)
        .order_by(StudentSkill.confidence_score.desc())
        .all()
    )

    return SkillsListResponse(
        resume_id=resume_id,
        skills=[SkillResponse.model_validate(s) for s in skills],
        total=len(skills),
    )


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/projects",
    response_model=ProjectsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project intelligence",
    description="Returns AI-analyzed project records. Only available after analysis completes.",
)
def get_projects(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ProjectsListResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    projects = (
        db.query(StudentProject)
        .filter(StudentProject.resume_id == resume_id)
        .order_by(StudentProject.complexity_score.desc())
        .all()
    )

    return ProjectsListResponse(
        resume_id=resume_id,
        projects=[ProjectResponse.model_validate(p) for p in projects],
        total=len(projects),
    )


# ---------------------------------------------------------------------------
# Internships
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/internships",
    response_model=InternshipsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get internship intelligence",
    description="Returns AI-analyzed internship records. Only available after analysis completes.",
)
def get_internships(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> InternshipsListResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    internships = (
        db.query(StudentInternship)
        .filter(StudentInternship.resume_id == resume_id)
        .all()
    )

    return InternshipsListResponse(
        resume_id=resume_id,
        internships=[InternshipResponse.model_validate(i) for i in internships],
        total=len(internships),
    )


# ---------------------------------------------------------------------------
# Certifications
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/certifications",
    response_model=CertificationsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get certification assessments",
    description="Returns AI-analyzed certification records. Only available after analysis completes.",
)
def get_certifications(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> CertificationsListResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    certs = (
        db.query(Certification)
        .filter(Certification.resume_id == resume_id)
        .all()
    )

    return CertificationsListResponse(
        resume_id=resume_id,
        certifications=[CertificationResponse.model_validate(c) for c in certs],
        total=len(certs),
    )


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/sections",
    response_model=SectionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detected resume sections",
    description=(
        "Returns the raw text sections detected in this resume. "
        "The 'contact' section is always removed to protect PII. "
        "contact_present indicates whether contact information was detected. "
        "Only available after analysis completes."
    ),
)
def get_sections(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> SectionsResponse:
    student = _get_student(db, current_user)
    resume = _get_owned_resume(db, resume_id, student.id)
    _require_completed(resume)

    raw_sections: dict = resume.extracted_sections or {}

    # Check for contact before stripping
    contact_present = "contact" in raw_sections and bool(raw_sections["contact"])

    # Return only safe section keys
    safe_sections = {
        k: v for k, v in raw_sections.items()
        if k in _SAFE_SECTION_KEYS
    }

    return SectionsResponse(
        resume_id=resume_id,
        contact_present=contact_present,
        sections=safe_sections,
    )
