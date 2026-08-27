"""
app/api/resume.py
-----------------
FastAPI route handlers for SkillFit Resume Upload System.

Endpoints:
    POST   /resume/upload      — Upload a resume (PDF or DOCX) with type
    GET    /resume             — List all resumes for the authenticated student
    GET    /resume/{resume_id} — Get metadata for a single resume
    DELETE /resume/{resume_id} — Delete a resume (file + DB record)

Phase history:
    Phase 3.2   — Initial upload, list, get, delete.
    Pre-3.6     — Upload now accepts resume_type (generic/specialized).
    Phase 3.13  — Pipeline auto-trigger REMOVED. Analysis is now admin-controlled.
                  Extraction router removed from this module's responsibilities.

Design (mirrors app/api/auth.py conventions):
    - Route handlers are intentionally thin. All business logic lives in
      app/services/resume_service.py.
    - Authentication is enforced via get_current_user from app/api/deps.py.
    - RBAC is enforced via require_roles(UserRole.student) — only students
      may upload or manage resumes.
    - Response models are declared explicitly on each route so FastAPI
      generates accurate OpenAPI schemas.
    - Multipart file uploads require python-multipart to be installed.

NOTE: These legacy routes remain for backward compatibility.
      New Phase 3.13 student routes live at /api/v1/resumes.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.enums import ResumeType, UserRole
from app.models.user import User
from app.schemas.resume import ResumeListResponse, ResumeResponse
from app.services import resume_service

router = APIRouter(prefix="/resume", tags=["Resume (Legacy)"])


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume (legacy route)",
    description=(
        "Upload a PDF or DOCX resume file with a specified type (generic or specialized). "
        "Validates file type, size (max 10 MB), and checks for duplicate uploads. "
        "If a resume of the same type already exists for this student, it is automatically "
        "replaced. Analysis is NOT triggered automatically — an Admin must trigger it via "
        "POST /api/v1/admin/resumes/{id}/analyze. "
        "Only accessible to authenticated student accounts."
    ),
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (.pdf or .docx, max 10 MB)."),
    resume_type: ResumeType = Form(
        ...,
        description=(
            "Category of this resume. "
            "Allowed values: 'generic' (general-purpose) or 'specialized' (role-targeted). "
            "Each student may have at most one resume per type; uploading a new one "
            "automatically replaces the existing resume of that type."
        ),
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ResumeResponse:
    return await resume_service.upload_resume(
        db, file, current_user.id, resume_type
    )


@router.get(
    "",
    response_model=ResumeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all uploaded resumes (legacy route)",
    description=(
        "Returns all resumes uploaded by the authenticated student, newest first. "
        "Only the authenticated student's own resumes are returned."
    ),
)
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ResumeListResponse:
    return resume_service.list_resumes(db, current_user.id)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific resume (legacy route)",
    description=(
        "Returns metadata for a single uploaded resume, including current processing_status. "
        "Ownership is strictly enforced — students cannot access another student's resume."
    ),
)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ResumeResponse:
    return resume_service.get_resume(db, resume_id, current_user.id)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resume (legacy route)",
    description=(
        "Permanently deletes a resume — both the physical file on disk and the "
        "database record. Ownership is strictly enforced. Returns 409 if analysis "
        "is currently running."
    ),
)
def delete_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> None:
    resume_service.delete_resume(db, resume_id, current_user.id)
