"""
app/services/extraction_service.py
----------------------------------
Business logic for SkillFit Phase 3.3 – Resume Text Extraction System.

Handles:
    - Re-validation of stored resume files (extension, signature, MIME, parser)
    - Path confinement verification (guarantees reading strictly inside UPLOAD_DIR)
    - Timeout-protected text extraction (MAX_EXTRACTION_SECONDS = 15)
    - Normalization and size validation (MAX_EXTRACTED_CHARS = 200_000)
    - Transactional persistence of extracted_text onto the ResumeFile ORM model
    - Fetching extracted text with ownership enforcement

Security & Integrity:
    - Read-only file access: never modifies, deletes, or executes the target file
    - No dynamic code execution (no eval/exec/os.system/subprocess)
    - No dynamic imports
    - Safe error reporting: hides filesystem paths and DB exceptions from responses
    - Strict logging: logs lifecycle and audit events without logging text/PII
"""

import concurrent.futures
import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.file_utils import (
    UPLOAD_DIR,
    validate_extension,
    validate_file_parseable,
    validate_file_signature,
    validate_file_size,
    validate_mime_type,
)
from app.models.resume_file import ResumeFile
from app.models.student import Student
from app.parsers.resume_parser import extract_resume_text
from app.schemas.extraction import ExtractedTextResponse, ExtractionResponse

logger = logging.getLogger(__name__)

# Maximum processing time allowed for a single resume extraction job
MAX_EXTRACTION_SECONDS: int = 15


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _get_student_or_403(db: Session, user_id: uuid.UUID) -> Student:
    """
    Fetch the Student profile for the given User UUID.

    Raises:
        HTTPException 403 — if no Student profile exists for this user.
    """
    student: Student | None = (
        db.query(Student).filter(Student.user_id == user_id).first()
    )
    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to student accounts.",
        )
    return student


def _get_owned_resume_or_404(
    db: Session, resume_id: uuid.UUID, student_id: int
) -> ResumeFile:
    """
    Fetch a ResumeFile record, enforcing strict student ownership.

    Raises:
        HTTPException 404 — resume not found.
        HTTPException 403 — resume exists but belongs to another student.
    """
    resume: ResumeFile | None = (
        db.query(ResumeFile).filter(ResumeFile.id == resume_id).first()
    )
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found.",
        )
    if resume.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resume.",
        )
    return resume


def _verify_file_confinement_and_readability(file_path: str, upload_dir: str = UPLOAD_DIR) -> str:
    """
    Verify that the target file path resides strictly inside the upload directory
    and is accessible for reading.

    Returns:
        Absolute normalized file path.

    Raises:
        HTTPException 400 — if the path attempts directory traversal.
        HTTPException 404 — if the file does not exist on disk.
        HTTPException 500 — if the file is unreadable.
    """
    abs_upload_dir = os.path.abspath(upload_dir)
    abs_file_path = os.path.abspath(file_path)

    # 1. Path confinement check
    if not abs_file_path.startswith(abs_upload_dir + os.sep):
        logger.error(
            "SECURITY: Directory traversal attempt detected. file_path=%s upload_dir=%s",
            abs_file_path,
            abs_upload_dir,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path.",
        )

    # 2. File existence check
    if not os.path.isfile(abs_file_path):
        logger.error("Physical resume file not found on disk: %s", abs_file_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical resume file could not be found on storage.",
        )

    # 3. Readability check
    if not os.access(abs_file_path, os.R_OK):
        logger.error("Physical resume file is not readable: %s", abs_file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resume file is not accessible for reading.",
        )

    return abs_file_path


def _revalidate_file_content(abs_file_path: str, extension: str) -> bytes:
    """
    Re-validate stored file against all security layers before extraction.

    Guarantees:
        - Extension is valid
        - File size is within bounds
        - Magic bytes match extension
        - MIME type matches
        - Basic parser integrity

    Returns:
        File bytes read in read-only mode.
    """
    try:
        with open(abs_file_path, "rb") as f:
            file_bytes = f.read()
    except OSError as exc:
        logger.error("Failed to read resume file %s: %s", abs_file_path, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read the resume file.",
        ) from exc

    try:
        validate_extension(abs_file_path)
        validate_file_size(len(file_bytes))
        validate_file_signature(file_bytes, extension)
        validate_mime_type(file_bytes, extension)
        validate_file_parseable(file_bytes, extension)
    except ValueError as exc:
        logger.warning("Security re-validation failed for %s: %s", abs_file_path, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return file_bytes


def _extract_with_timeout(abs_file_path: str) -> str:
    """
    Execute resume text extraction inside a worker thread with timeout protection.

    Raises:
        HTTPException 408 / 400 / 500 on timeout or extraction errors.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(extract_resume_text, abs_file_path)
        try:
            return future.result(timeout=MAX_EXTRACTION_SECONDS)
        except concurrent.futures.TimeoutError:
            logger.error(
                "Resume extraction timed out after %d seconds: %s",
                MAX_EXTRACTION_SECONDS,
                abs_file_path,
            )
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Resume extraction timed out. The file may be overly complex or corrupted.",
            )
        except ValueError as exc:
            logger.warning("Resume extraction validation error for %s: %s", abs_file_path, exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except Exception as exc:
            logger.error("Unexpected error during text extraction of %s: %s", abs_file_path, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during resume text extraction.",
            ) from exc


# ---------------------------------------------------------------------------
# Public Service Functions
# ---------------------------------------------------------------------------


def extract_resume(
    db: Session, resume_id: uuid.UUID, user_id: uuid.UUID
) -> ExtractionResponse:
    """
    Extract, normalize, and store text for a student's uploaded resume.

    Flow:
        1. Validate student account and resume ownership.
        2. Validate path confinement (uploads/resumes/) and readability.
        3. Re-validate file binary (signature, MIME, size, parseability).
        4. Extract and normalize text with timeout protection.
        5. Persist extracted_text to the ResumeFile database record.
        6. Commit transaction safely with rollback on failure.
        7. Return structured ExtractionResponse.
    """
    student = _get_student_or_403(db, user_id)
    resume = _get_owned_resume_or_404(db, resume_id, student.id)

    logger.info(
        "Starting text extraction for resume_id=%s, student_id=%s, file_type=%s",
        resume.id,
        student.id,
        resume.file_type,
    )

    # 1. Path confinement & existence
    abs_file_path = _verify_file_confinement_and_readability(resume.file_path, UPLOAD_DIR)

    # 2. Security re-validation
    _revalidate_file_content(abs_file_path, resume.file_type)

    # 3. Extract text with timeout protection
    extracted_text = _extract_with_timeout(abs_file_path)

    # 4. Save to database
    now = datetime.now(timezone.utc)
    resume.extracted_text = extracted_text
    resume.updated_at = now

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Failed to commit extracted text for resume_id=%s: %s", resume.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while saving extracted text.",
        ) from exc

    db.refresh(resume)

    char_count = len(extracted_text)
    word_count = len(extracted_text.split())

    logger.info(
        "Text extraction completed successfully: resume_id=%s, chars=%d, words=%d",
        resume.id,
        char_count,
        word_count,
    )

    return ExtractionResponse(
        resume_id=resume.id,
        character_count=char_count,
        word_count=word_count,
        status="completed",
        message="Text extracted and saved successfully.",
        extracted_at=resume.updated_at,
    )


# ---------------------------------------------------------------------------
# Internal Pipeline Function (Pre-Phase 3.6)
# ---------------------------------------------------------------------------


def extract_resume_internal(db: Session, resume: ResumeFile) -> None:
    """
    Extract, normalize, and persist text for a ResumeFile ORM object.

    This is the internal-only variant called by resume_pipeline.process_resume_pipeline().
    It accepts the ResumeFile ORM object directly — ownership validation is NOT
    performed here because the pipeline orchestrator already controls which
    resume records it processes.

    Security layers preserved (identical to extract_resume()):
        - Path confinement (file must be within UPLOAD_DIR)
        - File binary re-validation (signature, MIME, size, parseability)
        - Timeout-protected extraction (MAX_EXTRACTION_SECONDS = 15)

    Error handling:
        - Raises ValueError on any validation or extraction failure.
        - Raises RuntimeError on DB commit failure.
        - Does NOT raise HTTPException — this runs outside of a request context.

    Args:
        db:     SQLAlchemy session (pipeline-owned, not request-scoped).
        resume: ResumeFile ORM object loaded by the pipeline orchestrator.

    Side effects:
        - Sets resume.extracted_text to the normalized extracted content.
        - Updates resume.updated_at.
        - Commits the DB transaction.
    """
    logger.info(
        "Internal extraction started: resume_id=%s file_type=%s",
        resume.id,
        resume.file_type,
    )

    # 1. Path confinement & existence check
    try:
        abs_file_path = _verify_file_confinement_and_readability(resume.file_path, UPLOAD_DIR)
    except HTTPException as exc:
        raise ValueError(
            f"Path validation failed for resume_id={resume.id}: {exc.detail}"
        ) from exc

    # 2. Security re-validation of file binary
    try:
        _revalidate_file_content(abs_file_path, resume.file_type)
    except HTTPException as exc:
        raise ValueError(
            f"File re-validation failed for resume_id={resume.id}: {exc.detail}"
        ) from exc

    # 3. Extract text with timeout protection
    try:
        extracted_text = _extract_with_timeout(abs_file_path)
    except HTTPException as exc:
        raise ValueError(
            f"Text extraction failed for resume_id={resume.id}: {exc.detail}"
        ) from exc

    # 4. Persist to database
    now = datetime.now(timezone.utc)
    resume.extracted_text = extracted_text
    resume.updated_at = now

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(
            "DB commit failed during internal extraction for resume_id=%s: %s",
            resume.id,
            exc,
        )
        raise RuntimeError(
            f"Database error while saving extracted text for resume_id={resume.id}"
        ) from exc

    db.refresh(resume)

    char_count = len(extracted_text)
    word_count = len(extracted_text.split())
    logger.info(
        "Internal extraction completed: resume_id=%s chars=%d words=%d",
        resume.id,
        char_count,
        word_count,
    )



def get_extracted_text(
    db: Session, resume_id: uuid.UUID, user_id: uuid.UUID
) -> ExtractedTextResponse:
    """
    Retrieve previously extracted text for a specific resume.

    Flow:
        1. Validate student account and resume ownership.
        2. Verify that extracted_text has been generated.
        3. Return ExtractedTextResponse.

    Raises:
        HTTPException 400 — if text has not been extracted yet.
        HTTPException 403 — ownership violation.
        HTTPException 404 — resume not found.
    """
    student = _get_student_or_403(db, user_id)
    resume = _get_owned_resume_or_404(db, resume_id, student.id)

    if not resume.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text has not been extracted for this resume yet. Please call POST /resume/{resume_id}/extract first.",
        )

    char_count = len(resume.extracted_text)
    word_count = len(resume.extracted_text.split())

    return ExtractedTextResponse(
        resume_id=resume.id,
        file_name=resume.file_name,
        extracted_text=resume.extracted_text,
        character_count=char_count,
        word_count=word_count,
        extracted_at=resume.updated_at,
    )
