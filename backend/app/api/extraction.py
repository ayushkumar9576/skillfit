"""
app/api/extraction.py
---------------------
FastAPI route handlers for SkillFit Phase 3.3 – Resume Text Extraction System.

Endpoints:
    POST /resume/{resume_id}/extract — Trigger text extraction & normalization on an uploaded resume
    GET  /resume/{resume_id}/text    — Retrieve the extracted raw text for a specific resume

Design:
    - Route handlers are thin; all parsing, confinement checks, and DB logic
      reside in app/services/extraction_service.py.
    - Protected by JWT authentication and RBAC (require_roles(UserRole.student)).
    - Ownership validation ensures students can only extract and read their own resumes.
"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.enums import UserRole
from app.models.user import User
from app.schemas.extraction import ExtractedTextResponse, ExtractionResponse
from app.services import extraction_service

router = APIRouter(prefix="/resume", tags=["Resume Extraction"])


@router.post(
    "/{resume_id}/extract",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text from an uploaded resume",
    description=(
        "Parses the uploaded PDF or DOCX file, normalizes the text content, "
        "and saves it to the database record. Strictly accessible to the resume owner."
    ),
)
def extract_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ExtractionResponse:
    return extraction_service.extract_resume(db, resume_id, current_user.id)


@router.get(
    "/{resume_id}/text",
    response_model=ExtractedTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Get extracted resume text",
    description=(
        "Returns the extracted and normalized plain-text content of the resume. "
        "Requires the extraction endpoint to have been run first."
    ),
)
def get_extracted_text(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
) -> ExtractedTextResponse:
    return extraction_service.get_extracted_text(db, resume_id, current_user.id)
