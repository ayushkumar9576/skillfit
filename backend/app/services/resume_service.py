"""
app/services/resume_service.py
--------------------------------
Business logic for SkillFit Resume Upload System.

Phase history:
    Phase 3.2   — Upload, list, get, delete.
    Phase 3.2.1 — Security hardening (5-layer validation, path confinement).
    Pre-3.6     — Resume type system (generic/specialized), automatic replacement,
                  pipeline background trigger, processing_status lifecycle.

Handles:
    - Resume upload with type awareness (CHANGE-04)
    - Automatic replacement of same-type resume (CHANGE-05)
    - Pipeline background task trigger after upload (CHANGE-09/10/11)
    - Resume listing (student-scoped)
    - Resume retrieval by ID (ownership enforced)
    - Resume deletion (ownership enforced, file + DB record)

What this module does NOT do:
    - HTTP request/response handling (that belongs in app/api/resume.py)
    - Schema validation (Pydantic handles that before the service is called)
    - Text extraction or AI analysis (handled by resume_pipeline.py)

Error conventions (mirrors auth_service.py):
    - Raises fastapi.HTTPException directly so route handlers stay thin.
    - 400 Bad Request   — invalid file type, size, or empty content
    - 404 Not Found     — resume not found
    - 403 Forbidden     — ownership violation
    - 409 Conflict      — same hash re-upload attempt (exact duplicate content)
    - 500 via unhandled — unexpected DB/OS errors bubble up naturally
"""

import logging
import os
import uuid

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import ProcessingStatus, ResumeType
from app.core.file_utils import (
    MAX_RESUMES_PER_STUDENT,
    UPLOAD_DIR,
    ensure_upload_directory,
    generate_sha256,
    generate_storage_filename,
    safe_delete_file,
    validate_extension,
    validate_file_parseable,
    validate_file_signature,
    validate_file_size,
    validate_mime_type,
)
from app.models.resume_file import ResumeFile
from app.models.student import Student
from app.schemas.resume import ResumeListResponse, ResumeResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_student_or_403(db: Session, user_id: uuid.UUID) -> Student:
    """
    Fetch the Student profile for the given User UUID.

    Raises:
        HTTPException 403 — if no Student profile exists for this user.
            Using 403 (not 404) prevents leaking whether a student ID exists.
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
    Fetch a ResumeFile record, enforcing strict ownership.

    Raises:
        HTTPException 404 — resume not found (generic message prevents enumeration).
        HTTPException 403 — resume exists but belongs to a different student.
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


def _replace_existing_resume(db: Session, student_id: int, resume_type: ResumeType) -> None:
    """
    Delete any existing active resume of the given type for this student.

    Called before inserting the new resume record. This implements the
    automatic replacement behavior:
        - Deletes the physical file from disk (safe — logs if missing).
        - Deletes the database record.
        - Does NOT commit — the caller owns the transaction.

    If no existing resume of this type is found, this is a safe no-op.

    Args:
        db:          Active database session.
        student_id:  Integer student PK.
        resume_type: The resume type being replaced (generic or specialized).
    """
    existing: ResumeFile | None = (
        db.query(ResumeFile)
        .filter(
            ResumeFile.student_id == student_id,
            ResumeFile.resume_type == resume_type,
            ResumeFile.is_active.is_(True),
        )
        .first()
    )
    if existing is None:
        return

    logger.info(
        "Replacing existing %s resume: resume_id=%s student_id=%s",
        resume_type.value,
        existing.id,
        student_id,
    )

    # Delete physical file first (safe — logs on missing)
    safe_delete_file(existing.file_path)

    # Delete database record (cascade will also remove linked cv_analysis)
    db.delete(existing)
    # Flush so the DELETE reaches the DB before the caller's INSERT.
    # This is critical to avoid unique constraint violation on (student_id, resume_type)
    # when the new record is inserted within the same transaction.
    db.flush()
    logger.info(
        "Old %s resume removed from DB: resume_id=%s",
        resume_type.value,
        existing.id,
    )


# ---------------------------------------------------------------------------
# Upload Resume
# ---------------------------------------------------------------------------


async def upload_resume(
    db: Session,
    file: UploadFile,
    user_id: uuid.UUID,
    resume_type: ResumeType,
    background_tasks: BackgroundTasks,
) -> ResumeResponse:
    """
    Validate, store, and record an uploaded resume file, then trigger the
    automated processing pipeline as a background task.

    Flow:
        1.  Verify the user has a student profile.
        2.  Enforce resume count safety guard (MAX_RESUMES_PER_STUDENT = 2).
        3.  Read file bytes (required for all subsequent validation checks).
        4.  Validate extension (Layer 1 — cheapest gate).
        5.  Validate size (Layer 2 — empty / too large).
        6.  Validate file signature / magic bytes (Layer 3).
        7.  Validate MIME type via libmagic (Layer 4).
        8.  Validate file is parseable by the appropriate library (Layer 5).
        9.  Compute SHA-256 hash.
        10. Application-level duplicate content check (same hash = same bytes).
        11. Delete existing resume of this type if one exists (replacement logic).
        12. Generate a UUID-based storage filename.
        13. Ensure upload directory exists.
        14. Write file to disk.
        15. Create ResumeFile ORM record with processing_status='uploaded'.
        16. Commit transaction.
        17. Add pipeline background task.
        18. Return ResumeResponse (upload is immediately successful).

    Args:
        db:               SQLAlchemy session.
        file:             FastAPI UploadFile object from the multipart form.
        user_id:          UUID of the authenticated User (from JWT).
        resume_type:      Category of this resume (generic or specialized).
        background_tasks: FastAPI BackgroundTasks for deferred pipeline execution.

    Returns:
        ResumeResponse with the newly created record's metadata.

    Raises:
        HTTPException 400 — unsupported extension / empty file / file too large.
        HTTPException 403 — user has no student profile.
        HTTPException 409 — exact same resume content already uploaded by this student.
        HTTPException 500 — storage or unexpected DB failure.
    """
    # 1. Verify student profile
    student = _get_student_or_403(db, user_id)

    # 2. Safety guard: count active resumes (primary enforcement is type-aware replacement)
    active_count = (
        db.query(ResumeFile)
        .filter(
            ResumeFile.student_id == student.id,
            ResumeFile.is_active.is_(True),
        )
        .count()
    )
    # Only block if we are ALREADY at the limit AND there is no existing resume of this type
    # to replace (meaning this would create a 3rd resume, which is impossible under the rules).
    existing_of_type = (
        db.query(ResumeFile)
        .filter(
            ResumeFile.student_id == student.id,
            ResumeFile.resume_type == resume_type,
            ResumeFile.is_active.is_(True),
        )
        .first()
    )
    if active_count >= MAX_RESUMES_PER_STUDENT and existing_of_type is None:
        # Student already has 2 resumes of different types and is trying to add a 3rd
        logger.warning(
            "Student %s hit resume upload limit (%d/%d) with no replacement target.",
            student.id,
            active_count,
            MAX_RESUMES_PER_STUDENT,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Resume limit reached. You may store a maximum of "
                f"{MAX_RESUMES_PER_STUDENT} resumes (1 generic + 1 specialized). "
                "Please delete an existing resume before uploading a new one."
            ),
        )

    # 3. Read bytes (must be done before validation to get size)
    file_bytes = await file.read()

    # 4. Validate extension (Layer 1)
    try:
        extension = validate_extension(file.filename or "")
    except ValueError as exc:
        logger.warning(
            "Student %s upload rejected — invalid extension: %s",
            student.id,
            file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # 5. Validate size (Layer 2)
    try:
        validate_file_size(len(file_bytes))
    except ValueError as exc:
        logger.warning(
            "Student %s upload rejected — size validation: %s (%d bytes)",
            student.id,
            file.filename,
            len(file_bytes),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # 6. Validate file signature / magic bytes (Layer 3)
    try:
        validate_file_signature(file_bytes, extension)
    except ValueError as exc:
        logger.warning(
            "Student %s upload rejected — signature mismatch: %s",
            student.id,
            file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # 7. Validate MIME type (Layer 4)
    try:
        validate_mime_type(file_bytes, extension)
    except ValueError as exc:
        logger.warning(
            "Student %s upload rejected — MIME type mismatch: %s",
            student.id,
            file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # 8. Validate file is parseable (Layer 5 — deepest gate)
    try:
        validate_file_parseable(file_bytes, extension)
    except ValueError as exc:
        logger.warning(
            "Student %s upload rejected — parser validation failed: %s",
            student.id,
            file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # 9. Compute SHA-256
    file_hash = generate_sha256(file_bytes)

    # 10. Application-level duplicate content check
    # Check for same hash across ALL resume types for this student
    hash_duplicate = (
        db.query(ResumeFile)
        .filter(
            ResumeFile.student_id == student.id,
            ResumeFile.file_hash == file_hash,
        )
        .first()
    )
    if hash_duplicate:
        logger.info(
            "Student %s attempted to re-upload duplicate resume content (hash=%s).",
            student.id,
            file_hash,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This resume has already been uploaded. "
                "Please upload a different or updated version."
            ),
        )

    # 11. Replace existing resume of this type (if one exists)
    _replace_existing_resume(db, student.id, resume_type)

    # 12. Generate safe storage filename
    storage_filename = generate_storage_filename(extension)

    # 13. Ensure upload directory exists
    upload_dir = ensure_upload_directory(UPLOAD_DIR)
    file_path = os.path.join(upload_dir, storage_filename)

    # 14. Write file to disk
    try:
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        logger.info(
            "Resume stored on disk for student %s: %s",
            student.id,
            file_path,
        )
    except OSError as exc:
        logger.error(
            "Failed to write resume to disk for student %s: %s",
            student.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store the uploaded file. Please try again.",
        ) from exc

    # 15. Create database record
    resume_id = uuid.uuid4()
    resume = ResumeFile(
        id=resume_id,
        student_id=student.id,
        file_name=file.filename,
        file_path=file_path,
        file_type=extension,
        file_size=len(file_bytes),
        file_hash=file_hash,
        resume_type=resume_type,
        processing_status=ProcessingStatus.uploaded,
        # extracted_text is intentionally NOT populated here — pipeline handles it
    )
    db.add(resume)

    # 16. Commit transaction (DB unique constraint is the last safety net)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Clean up the file we just wrote to disk
        safe_delete_file(file_path)
        logger.error(
            "DB IntegrityError (race condition or type conflict) for student %s, hash %s.",
            student.id,
            file_hash,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This resume has already been uploaded. "
                "Please upload a different or updated version."
            ),
        )

    db.refresh(resume)
    logger.info(
        "Resume uploaded successfully: resume_id=%s student_id=%s type=%s filename=%s size=%d bytes",
        resume.id,
        student.id,
        resume_type.value,
        file.filename,
        len(file_bytes),
    )

    # 17. Trigger automated pipeline as a background task
    # Import here to avoid circular imports at module load time
    from app.services.resume_pipeline import process_resume_pipeline
    background_tasks.add_task(process_resume_pipeline, resume.id)
    logger.info(
        "Pipeline background task queued: resume_id=%s", resume.id
    )

    # 18. Return immediate upload success response
    return ResumeResponse.model_validate(resume)


# ---------------------------------------------------------------------------
# List Resumes
# ---------------------------------------------------------------------------


def list_resumes(db: Session, user_id: uuid.UUID) -> ResumeListResponse:
    """
    Return all active resumes owned by the authenticated student, newest first.

    Args:
        db:      SQLAlchemy session.
        user_id: UUID of the authenticated User.

    Returns:
        ResumeListResponse with the list and count of resumes.

    Raises:
        HTTPException 403 — user has no student profile.
    """
    student = _get_student_or_403(db, user_id)

    resumes = (
        db.query(ResumeFile)
        .filter(
            ResumeFile.student_id == student.id,
            ResumeFile.is_active.is_(True),
        )
        .order_by(ResumeFile.created_at.desc())
        .all()
    )

    resume_responses = [ResumeResponse.model_validate(r) for r in resumes]
    return ResumeListResponse(resumes=resume_responses, total=len(resume_responses))


# ---------------------------------------------------------------------------
# Get Resume By ID
# ---------------------------------------------------------------------------


def get_resume(
    db: Session, resume_id: uuid.UUID, user_id: uuid.UUID
) -> ResumeResponse:
    """
    Return metadata for a single resume owned by the authenticated student.

    Args:
        db:        SQLAlchemy session.
        resume_id: UUID of the target ResumeFile record.
        user_id:   UUID of the authenticated User.

    Returns:
        ResumeResponse for the requested record.

    Raises:
        HTTPException 403 — user has no student profile or does not own resume.
        HTTPException 404 — resume not found.
    """
    student = _get_student_or_403(db, user_id)
    resume = _get_owned_resume_or_404(db, resume_id, student.id)
    return ResumeResponse.model_validate(resume)


# ---------------------------------------------------------------------------
# Delete Resume
# ---------------------------------------------------------------------------


def delete_resume(
    db: Session, resume_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """
    Delete a resume record and its corresponding physical file.

    Ownership is strictly enforced — a student cannot delete another
    student's resume.

    Flow:
        1. Verify student profile.
        2. Fetch and verify ownership of the resume.
        3. Delete physical file from disk (safe — logs if already missing).
        4. Delete database record.
        5. Commit transaction.

    Args:
        db:        SQLAlchemy session.
        resume_id: UUID of the target ResumeFile record.
        user_id:   UUID of the authenticated User.

    Raises:
        HTTPException 403 — user has no student profile or does not own resume.
        HTTPException 404 — resume not found.
    """
    student = _get_student_or_403(db, user_id)
    resume = _get_owned_resume_or_404(db, resume_id, student.id)

    file_path = resume.file_path
    resume_id_log = resume.id

    # 3. Delete physical file (safe — does not raise on missing file)
    safe_delete_file(file_path)

    # 4. Delete database record
    db.delete(resume)

    # 5. Commit
    db.commit()

    logger.info(
        "Resume deleted: resume_id=%s student_id=%s",
        resume_id_log,
        student.id,
    )
