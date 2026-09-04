"""
app/api/v1/drives.py
---------------------
Phase 4.1 + Phase 4.2 — Placement Drive Intelligence API.

Endpoints:
    Phase 4.1 (Drive CRUD + Snapshot foundation):
        POST   /api/v1/drives              Create a Placement Drive
        GET    /api/v1/drives              List Placement Drives
        GET    /api/v1/drives/{id}         Get a single Placement Drive
        PATCH  /api/v1/drives/{id}         Partially update a Drive
        GET    /api/v1/drives/{id}/snapshot Get latest Drive Intelligence Snapshot

    Phase 4.2 (Drive Ingestion & Parsing):
        POST   /api/v1/drives/{id}/upload          Upload a PDF job description
        POST   /api/v1/drives/{id}/text            Submit raw text job description
        GET    /api/v1/drives/{id}/content/latest  Retrieve latest normalised content
        GET    /api/v1/drives/{id}/sources         List all source versions for a drive
        GET    /api/v1/drives/{id}/sources/{src}   Retrieve a specific source record

Phase 4.2 design:
    - Upload and text endpoints are separate for cleaner validation and OpenAPI docs.
    - Ingestion service handles all pipeline stages — the router delegates entirely.
    - Error responses are structured and never expose stack traces or internal paths.
    - Security events are logged in the service layer; the router returns clean 4xx.

Deferred to later phases:
    - POST /api/v1/drives/{id}/analyze  (Phase 4.3 — intelligence pipeline trigger)
    - GET  /api/v1/drives/{id}/analysis (Phase 4.3 — analysis tracking)

Auth:
    - Drive creation, updates, and ingestion require admin role.
    - Drive and source retrieval is accessible to admin and faculty roles.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.enums import DriveStatus, UserRole
from app.core.security.scanner import ScanError
from app.models.user import User
from app.schemas.drive_schemas import (
    DriveCreateRequest,
    DriveListResponse,
    DriveResponse,
    DriveSnapshotResponse,
    DriveUpdateRequest,
)
from app.schemas.drive_source_schemas import (
    DriveSourceListResponse,
    DriveSourceResponse,
    IngestionResponse,
    ParsedContentResponse,
    TextSubmissionRequest,
)
from app.services import drive_service
from app.services import drive_ingestion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/drives", tags=["Drives"])


# ===========================================================================
# Phase 4.1 — Drive CRUD
# ===========================================================================


@router.post("", response_model=DriveResponse, status_code=status.HTTP_201_CREATED)
def create_drive(
    data: DriveCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """
    Create a new Placement Drive.

    Requires admin role. The drive is created in `draft` status by default.
    Intelligence generation (Phase 4.3) is not triggered at creation time.
    """
    drive = drive_service.create_drive(db, data)
    return drive


@router.get("", response_model=DriveListResponse)
def list_drives(
    status_filter: Optional[DriveStatus] = Query(
        None,
        alias="status",
        description="Filter drives by lifecycle status.",
    ),
    skip: int = Query(0, ge=0, description="Pagination offset."),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit."),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    List Placement Drives with optional status filtering and pagination.

    Accessible to admin and faculty roles.
    """
    drives = drive_service.list_drives(db, status=status_filter, skip=skip, limit=limit)
    return DriveListResponse(drives=drives, total=len(drives))


@router.get("/{drive_id}", response_model=DriveResponse)
def get_drive(
    drive_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    Retrieve a single Placement Drive by its integer ID.

    Returns 404 if the drive does not exist.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )
    return drive


@router.patch("/{drive_id}", response_model=DriveResponse)
def update_drive(
    drive_id: int,
    data: DriveUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """
    Partially update a Placement Drive.

    Only provided fields are updated (PATCH semantics). Requires admin role.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )
    updated = drive_service.update_drive(db, drive, data)
    return updated


# ---------------------------------------------------------------------------
# Phase 4.1 — Snapshot Retrieval Foundation
# ---------------------------------------------------------------------------


@router.get("/{drive_id}/snapshot", response_model=DriveSnapshotResponse)
def get_drive_snapshot(
    drive_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    Retrieve the latest Drive Intelligence Snapshot for a given drive.

    Phase 4.1: Returns 404 until Phase 4.3 populates snapshots via the
    intelligence pipeline.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )

    snapshot = drive_service.get_latest_drive_snapshot(db, drive_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No intelligence snapshot found for drive {drive_id}. "
                "Drive intelligence generation is available from Phase 4.3."
            ),
        )

    return DriveSnapshotResponse(
        id=str(snapshot.id),
        drive_id=snapshot.drive_id,
        snapshot_version=snapshot.snapshot_version,
        analysis_version=snapshot.analysis_version,
        intelligence_payload=snapshot.intelligence_payload,
        metadata_payload=snapshot.metadata_payload,
        created_at=snapshot.created_at,
    )


# ===========================================================================
# Phase 4.2 — Drive Ingestion & Parsing
# ===========================================================================


# ---------------------------------------------------------------------------
# Upload PDF
# ---------------------------------------------------------------------------


@router.post(
    "/{drive_id}/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF job description for a drive.",
)
def upload_drive_pdf(
    drive_id: int,
    file: UploadFile = File(..., description="PDF job description file."),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """
    Upload and ingest a PDF job description for a Placement Drive.

    The file is validated (size, extension, MIME type, PDF integrity),
    extracted via pdfplumber, normalised, and persisted as a new versioned
    DriveSource record.

    If the same content has been uploaded before, a new version is still
    created and flagged as a duplicate in the response.

    Requires admin role.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )

    logger.info(
        "UPLOAD_STARTED drive_id=%d filename=%r content_type=%r",
        drive_id, file.filename, file.content_type,
    )

    try:
        parsed = drive_ingestion_service.ingest_pdf_upload(db, drive, file)
    except ValueError as exc:
        logger.warning(
            "UPLOAD_REJECTED drive_id=%d filename=%r reason=%s",
            drive_id, file.filename, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except ScanError as exc:
        logger.error(
            "SECURITY_EVENT:SCAN_FAILED drive_id=%d filename=%r error=%s",
            drive_id, file.filename, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File failed security scan. Upload rejected.",
        )
    except RuntimeError as exc:
        logger.error(
            "UPLOAD_EXTRACTION_FAILED drive_id=%d filename=%r error=%s",
            drive_id, file.filename, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    logger.info(
        "UPLOAD_COMPLETED drive_id=%d source_id=%s version=%d chars=%d",
        drive_id, parsed.source_id, parsed.source_version, parsed.statistics.character_count,
    )

    return IngestionResponse(
        message="Job description PDF uploaded and parsed successfully.",
        drive_id=drive_id,
        source_id=parsed.source_id,
        source_version=parsed.source_version,
        source_format=parsed.source_metadata.source_format,
        character_count=parsed.statistics.character_count,
        word_count=parsed.statistics.word_count,
        is_duplicate=parsed.is_duplicate,
        duplicate_of_version=parsed.duplicate_of_version,
        parser_version=parsed.source_metadata.parser_version,
        extractor_version=parsed.source_metadata.extractor_version,
    )


# ---------------------------------------------------------------------------
# Submit raw text
# ---------------------------------------------------------------------------


@router.post(
    "/{drive_id}/text",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit raw text job description for a drive.",
)
def submit_drive_text(
    drive_id: int,
    data: TextSubmissionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """
    Submit a raw text job description for a Placement Drive.

    The text is validated (size, minimum length), passed through the standard
    extraction and normalisation pipeline, and persisted as a new versioned
    DriveSource record.

    Requires admin role.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )

    logger.info(
        "TEXT_SUBMISSION_STARTED drive_id=%d length=%d chars",
        drive_id, len(data.text),
    )

    try:
        parsed = drive_ingestion_service.ingest_text_submission(db, drive, data.text)
    except ValueError as exc:
        logger.warning(
            "TEXT_SUBMISSION_REJECTED drive_id=%d reason=%s", drive_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except ScanError as exc:
        logger.error(
            "SECURITY_EVENT:SCAN_FAILED drive_id=%d text_submission error=%s",
            drive_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Content failed security scan. Submission rejected.",
        )
    except RuntimeError as exc:
        logger.error(
            "TEXT_SUBMISSION_FAILED drive_id=%d error=%s", drive_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    logger.info(
        "TEXT_SUBMISSION_COMPLETED drive_id=%d source_id=%s version=%d chars=%d",
        drive_id, parsed.source_id, parsed.source_version, parsed.statistics.character_count,
    )

    return IngestionResponse(
        message="Job description text submitted and parsed successfully.",
        drive_id=drive_id,
        source_id=parsed.source_id,
        source_version=parsed.source_version,
        source_format=parsed.source_metadata.source_format,
        character_count=parsed.statistics.character_count,
        word_count=parsed.statistics.word_count,
        is_duplicate=parsed.is_duplicate,
        duplicate_of_version=parsed.duplicate_of_version,
        parser_version=parsed.source_metadata.parser_version,
        extractor_version=parsed.source_metadata.extractor_version,
    )


# ---------------------------------------------------------------------------
# Retrieve latest parsed content
# ---------------------------------------------------------------------------


@router.get(
    "/{drive_id}/content/latest",
    response_model=ParsedContentResponse,
    summary="Retrieve the latest normalised job description content.",
)
def get_latest_content(
    drive_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    Retrieve the latest normalised job description content for a drive.

    Returns the normalized_content field from the most recent DriveSource
    record along with source provenance and content statistics.

    This is the Phase 4.3 input — the Drive Intelligence Engine will read
    normalized content from here, never from raw PDFs.

    Returns 404 if no source has been ingested yet.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )

    source = drive_ingestion_service.get_latest_drive_source(db, drive_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No parsed content found for drive {drive_id}. "
                "Upload a job description first using POST /upload or POST /text."
            ),
        )

    if not source.normalized_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Source v{source.version} exists but has no normalized content.",
        )

    meta = source.processing_metadata or {}

    return ParsedContentResponse(
        drive_id=drive_id,
        source_id=str(source.id),
        source_version=source.version,
        source_format=source.source_format,
        original_filename=source.original_filename,
        content_hash=source.content_hash,
        extractor_version=source.extractor_version,
        parser_version=source.parser_version,
        normalized_content=source.normalized_content,
        character_count=source.character_count,
        word_count=source.word_count,
        is_duplicate=meta.get("is_duplicate", False),
        duplicate_of_version=meta.get("duplicate_of_version"),
        created_at=source.created_at,
        processed_at=source.processed_at,
    )


# ---------------------------------------------------------------------------
# List all source versions
# ---------------------------------------------------------------------------


@router.get(
    "/{drive_id}/sources",
    response_model=DriveSourceListResponse,
    summary="List all source versions for a drive.",
)
def list_drive_sources(
    drive_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    List all DriveSource records for a drive, ordered by version ascending.

    Provides full audit history of all job description uploads and
    text submissions for a given drive.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )

    sources = drive_ingestion_service.list_drive_sources(db, drive_id)
    return DriveSourceListResponse(
        drive_id=drive_id,
        sources=[DriveSourceResponse.from_orm_with_id(s) for s in sources],
        total=len(sources),
    )


# ---------------------------------------------------------------------------
# Get specific source by ID
# ---------------------------------------------------------------------------


@router.get(
    "/{drive_id}/sources/{source_id}",
    response_model=DriveSourceResponse,
    summary="Retrieve a specific source record by UUID.",
)
def get_drive_source(
    drive_id: int,
    source_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    Retrieve a specific DriveSource record by its UUID.

    Validates that the source belongs to the specified drive.
    Returns 404 if not found or if the source does not belong to this drive.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )

    source = drive_ingestion_service.get_drive_source_by_id(db, source_id)
    if not source or source.drive_id != drive_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source {source_id} not found for drive {drive_id}.",
        )

    return DriveSourceResponse.from_orm_with_id(source)
