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
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from datetime import date

from app.analysis.engines.executor import AnalysisExecutor

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
from app.services import drive_analysis_service
from app.schemas.drive_analysis_schemas import (
    AnalyzeDriveRequest,
    AnalysisListResponse,
    AnalysisResponse,
    SnapshotDetailResponse,
    SnapshotListResponse,
    SnapshotSummaryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/drives", tags=["Drives"])


# ===========================================================================
# Phase 4.1 — Drive CRUD
# ===========================================================================


def drive_create_form_dep(
    company_name: str = Form(...),
    role: str = Form(...),
    placement_season: str = Form(...),
    job_type: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    package: Optional[str] = Form(None),
    eligibility_criteria: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    application_deadline: Optional[date] = Form(None),
) -> DriveCreateRequest:
    from pydantic import ValidationError
    from fastapi.exceptions import RequestValidationError
    
    try:
        return DriveCreateRequest(
            company_name=company_name,
            role=role,
            placement_season=placement_season,
            job_type=job_type,
            location=location,
            package=package,
            eligibility_criteria=eligibility_criteria,
            description=description,
            application_deadline=application_deadline,
        )
    except ValidationError as e:
        raise RequestValidationError(e.errors())

@router.post("", response_model=DriveResponse, status_code=status.HTTP_201_CREATED)
def create_drive(
    data: DriveCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """
    Create a new Placement Drive via JSON.

    Requires admin role. A drive is created as a draft. JD upload and analysis 
    will be triggered via separate endpoints.
    """
    try:
        drive = drive_service.create_drive(db=db, data=data, commit=True)
    except drive_service.DuplicateDriveError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

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
    user: User = Depends(require_roles(UserRole.admin, UserRole.faculty, UserRole.student)),
):
    """
    List Placement Drives with optional status filtering and pagination.

    Accessible to admin, faculty, and student roles.
    Students only ever see PUBLISHED drives.
    """
    if user.role == UserRole.student:
        status_filter = DriveStatus.published

    drives = drive_service.list_drives(db, status=status_filter, skip=skip, limit=limit)
    return DriveListResponse(drives=drives, total=len(drives))


@router.get("/{drive_id}", response_model=DriveResponse)
def get_drive(
    drive_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.faculty, UserRole.student)),
):
    """
    Retrieve a single Placement Drive by its integer ID.

    Returns 404 if the drive does not exist, or if accessed by a student
    and the drive is not published.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )
        
    if user.role == UserRole.student and drive.status != DriveStatus.published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )
        
    return drive


@router.patch("/{drive_id}", response_model=DriveResponse)
def update_drive(
    drive_id: UUID,
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
    
    try:
        updated = drive_service.update_drive(db, drive, data)
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except drive_service.DuplicateDriveError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


# ---------------------------------------------------------------------------
# Phase 4.1 — Snapshot Retrieval Foundation
# ---------------------------------------------------------------------------


@router.get("/{drive_id}/snapshot", response_model=DriveSnapshotResponse)
def get_drive_snapshot(
    drive_id: UUID,
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
    drive_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF job description file."),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """
    Upload and ingest a revised PDF job description for a Placement Drive.

    A JD Revision immediately transitions the drive to ANALYZING and invalidates
    any prior publication. Requires admin role.
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
    drive_id: UUID,
    data: TextSubmissionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """
    Submit a raw text job description for a Placement Drive.

    A JD Revision immediately transitions the drive to ANALYZING and invalidates
    any prior publication. Requires admin role.
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
    drive_id: UUID,
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
    drive_id: UUID,
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
    drive_id: UUID,
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


# ===========================================================================
# Phase 4.3 — Drive Intelligence Analysis & Snapshots
# ===========================================================================


@router.post(
    "/{drive_id}/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger Drive Intelligence Analysis",
)
async def analyze_drive(
    drive_id: UUID,
    background_tasks: BackgroundTasks,
    body: AnalyzeDriveRequest = AnalyzeDriveRequest(),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """
    Trigger the Drive Intelligence Engine for the drive's latest ingested source.

    Flow:
        DriveSource (latest version)
              ↓
        ParsedDriveContent reconstruction
              ↓
        DriveIntelligenceEngine (LLM + Governance Layer)
              ↓
        DriveSnapshot (immutable intelligence record)

    This is an asynchronous operation. A DriveAnalysis record is created immediately
    with status PENDING. The execution is handed off to the AnalysisExecutor (via
    FastAPI BackgroundTasks), which transitions it to RUNNING and eventually
    COMPLETED or FAILED.

    Auth: admin only.
    """
    # 1. Create the analysis record synchronously (handles idempotency inside service)
    analysis = drive_analysis_service.create_analysis_record(
        db,
        drive_id,
        prompt_version=body.prompt_version,
    )
    
    # Transition the drive to analyzing state
    drive = drive_service.get_drive(db, drive_id)
    if drive and drive.status in [DriveStatus.draft, DriveStatus.analysis_failed, DriveStatus.ready]:
        drive.status = DriveStatus.analyzing
        
    db.commit()
    db.refresh(analysis)

    # 2. Handoff to executor abstraction
    executor = AnalysisExecutor(background_tasks)
    executor.submit_analysis(analysis.id)

    # 3. Return 202 ACCEPTED immediately
    return AnalysisResponse.model_validate(analysis)


@router.post(
    "/{drive_id}/cancel-analysis",
    status_code=status.HTTP_200_OK,
    summary="Cancel Drive Intelligence Analysis",
)
def cancel_analysis(
    drive_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    """
    Cancel an ongoing drive intelligence analysis by marking the drive status as analysis_failed.
    This allows the user to easily restart a stuck or unwanted analysis.
    """
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )
        
    if drive.status == DriveStatus.analyzing:
        drive.status = DriveStatus.analysis_failed
        db.commit()
        return {"message": "Analysis cancelled and marked as failed."}
    
    return {"message": "Drive is not currently analyzing."}


@router.get(
    "/{drive_id}/analysis",
    response_model=AnalysisListResponse,
    summary="Get Drive Intelligence Analysis History",
)
def get_analysis_history(
    drive_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    List all Drive Intelligence analysis execution records for a drive.

    Ordered newest first. Each record shows status, model, prompt version,
    token usage, quality score, and any failure reason.

    Auth: admin, faculty.
    """
    # Validate drive exists
    from app.models.drive import Drive
    drive = db.get(Drive, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )

    analyses = drive_analysis_service.get_analysis_history(db, drive_id, limit=limit)
    return AnalysisListResponse(
        drive_id=drive_id,
        total=len(analyses),
        analyses=[AnalysisResponse.model_validate(a) for a in analyses],
    )


@router.get(
    "/{drive_id}/snapshots",
    response_model=SnapshotListResponse,
    summary="List Drive Intelligence Snapshots",
)
def list_snapshots(
    drive_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    List all Drive Intelligence snapshots for a drive, newest first.

    Snapshots are immutable — each represents the intelligence state at
    the time of a specific analysis run. Use GET /snapshots/{id} for
    the full intelligence_payload.

    Auth: admin, faculty.
    """
    from sqlalchemy import desc
    from app.models.drive_snapshot import DriveSnapshotModel

    snapshots = (
        db.query(DriveSnapshotModel)
        .filter(DriveSnapshotModel.drive_id == drive_id)
        .order_by(desc(DriveSnapshotModel.created_at))
        .all()
    )
    return SnapshotListResponse(
        drive_id=drive_id,
        total=len(snapshots),
        snapshots=[SnapshotSummaryResponse.model_validate(s) for s in snapshots],
    )


@router.get(
    "/{drive_id}/snapshots/latest",
    response_model=SnapshotDetailResponse,
    summary="Get Latest Drive Intelligence Snapshot",
)
def get_latest_snapshot(
    drive_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    Retrieve the most recent Drive Intelligence snapshot for a drive.
    Returns 404 if no snapshots exist.
    """
    from sqlalchemy import desc
    from app.models.drive_snapshot import DriveSnapshotModel

    snapshot = (
        db.query(DriveSnapshotModel)
        .filter(DriveSnapshotModel.drive_id == drive_id)
        .order_by(desc(DriveSnapshotModel.created_at))
        .first()
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No snapshots found for drive {drive_id}.",
        )
    return SnapshotDetailResponse.model_validate(snapshot)


@router.get(
    "/{drive_id}/snapshots/{snapshot_id}",
    response_model=SnapshotDetailResponse,
    summary="Get Drive Intelligence Snapshot Detail",
)
def get_snapshot(
    drive_id: UUID,
    snapshot_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    Retrieve a specific Drive Intelligence snapshot by ID.

    Returns the full intelligence_payload containing:
        - technologies, technical_competencies, behavioral_competencies
        - qualifications, hiring_signals, role_expectations
        - selection_process, risks, success_indicators

    Auth: admin, faculty.
    """
    snapshot = drive_analysis_service.get_snapshot_by_id(db, drive_id, snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found for drive {drive_id}.",
        )
    return SnapshotDetailResponse.model_validate(snapshot)

# --- Phase 5.3C Recommendation Endpoint ---

from app.schemas.matching import RecommendedCandidateResponse
from app.matching.services.recommendation_service import RecommendationService
from app.models.resume_file import ResumeFile
from app.models.student import Student
from app.models.user import User as UserModel

@router.get(
    "/{drive_id}/recommended-candidates",
    response_model=List[RecommendedCandidateResponse],
    summary="Get Recommended Candidates",
)
def get_drive_recommended_candidates(
    drive_id: UUID,
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    Retrieve ranked candidate recommendations for a specific Placement Drive.
    Auth: admin, faculty.
    """
    # 1. Validate drive exists
    drive = drive_service.get_drive(db, drive_id)
    if not drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drive {drive_id} not found.",
        )
        
    # 2. Fetch recommendations
    try:
        match_results = RecommendationService.get_recommended_candidates(db, str(drive_id))
    except ValueError:
        return []
        
    if not match_results:
        return []
        
    # 3. Hydrate DTOs (Batch load resumes -> students)
    resume_ids = [UUID(res.candidate_id) for res in match_results]
    
    # We join ResumeFile -> Student to get the name
    resumes = db.query(ResumeFile, Student).join(Student, ResumeFile.student_id == Student.id).filter(ResumeFile.id.in_(resume_ids)).all()
    
    resume_map = {r[0].id: r for r in resumes}
    
    response = []
    for res in match_results:
        r_id = UUID(res.candidate_id)
        if r_id not in resume_map:
            continue
            
        resume_model, student_model = resume_map[r_id]
        
        # User model join isn't strictly necessary if Student model has the name,
        # but let's check what student_model has.
        # Actually, Student has user_id, User has full_name.
        # Let's batch load users as well.
        pass
        
    # We need full names. Let's do a better batch query.
    resumes_with_names = (
        db.query(ResumeFile.id, UserModel.full_name)
        .join(Student, ResumeFile.student_id == Student.id)
        .join(UserModel, Student.user_id == UserModel.id)
        .filter(ResumeFile.id.in_(resume_ids))
        .all()
    )
    name_map = {r[0]: r[1] for r in resumes_with_names}
    
    for res in match_results:
        r_id = UUID(res.candidate_id)
        if r_id not in name_map:
            continue
            
        top_strengths = [s.title.replace("Strong ", "") for s in res.explanation.strengths[:3]]
        top_gaps = [g.title.replace("Missing ", "") for g in res.explanation.gaps[:3]]
            
        response.append(
            RecommendedCandidateResponse(
                candidate_id=r_id,
                student_name=name_map[r_id],
                score=res.score.overall_score,
                tier=res.match_tier.value + "_MATCH",
                strengths=top_strengths,
                gaps=top_gaps,
                overall_narrative=res.explanation.overall_narrative
            )
        )
        
    return response
