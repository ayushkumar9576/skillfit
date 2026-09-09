"""
app/services/drive_service.py
------------------------------
Phase 4.1 — Placement Drive Intelligence Foundation Service.

Single responsibility: Drive entity lifecycle management and Drive Intelligence
snapshot persistence/retrieval.

Design contracts:
    - Follows the same API → Service → SQLAlchemy Session pattern as all other
      services in this project. No repository layer.
    - This service NEVER calls db.commit() or db.rollback() inside snapshot
      operations — that mirrors analysis_persistence_service.py conventions.
      Drive CRUD operations (create/update) DO commit since they are top-level
      transactional operations.
    - No intelligence generation logic exists here. Phase 4.3 will add
      intelligence pipeline invocation.

Phase roadmap for this file:
    Phase 4.1  — Drive CRUD + snapshot storage/retrieval foundation.
    Phase 4.3  — Add trigger_intelligence_pipeline(), update snapshot on completion.
    Phase 5    — Add get_drive_profile_for_matching() used by Matching Engine.
"""

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Any
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import DriveStatus, DriveSourceType
from app.models.drive import Drive
from app.models.drive_snapshot import DriveSnapshotModel
from app.schemas.drive_schemas import DriveCreateRequest, DriveUpdateRequest

logger = logging.getLogger(__name__)


class DuplicateDriveError(Exception):
    """Raised when a unique fingerprint constraint is violated."""
    pass


def generate_drive_fingerprint(company: str, role: str, season: str) -> str:
    """
    Generate a deterministic SHA-256 fingerprint for a placement drive
    based on normalized company name, role, and placement season.
    """
    norm_comp = re.sub(r'\s+', ' ', company.lower().strip())
    norm_role = re.sub(r'\s+', ' ', role.lower().strip())
    norm_season = season.strip().upper()
    
    raw_key = f"{norm_comp}|{norm_role}|{norm_season}"
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


# ---------------------------------------------------------------------------
# Drive CRUD
# ---------------------------------------------------------------------------


VALID_TRANSITIONS = {
    DriveStatus.draft: {DriveStatus.analyzing},
    DriveStatus.analyzing: {DriveStatus.ready, DriveStatus.analysis_failed},
    DriveStatus.analysis_failed: {DriveStatus.analyzing},
    DriveStatus.ready: {DriveStatus.published, DriveStatus.archived, DriveStatus.analyzing},
    DriveStatus.published: {DriveStatus.archived, DriveStatus.analyzing},
    DriveStatus.archived: set(),
}

def create_drive(db: Session, data: DriveCreateRequest, commit: bool = True) -> Drive:
    """
    Create and persist a new Placement Drive.

    Commits the transaction before returning. The new Drive will have
    status=draft and source_type=manual by default (configurable via data).

    Args:
        db:   Active SQLAlchemy session.
        data: Validated DriveCreateRequest payload.

    Returns:
        The newly created Drive ORM object.
    """
    fingerprint = generate_drive_fingerprint(data.company_name, data.role, data.placement_season)

    drive = Drive(
        company_name=data.company_name,
        role=data.role,
        placement_season=data.placement_season,
        drive_fingerprint=fingerprint,
        job_type=data.job_type,
        location=data.location,
        package=data.package,
        eligibility_criteria=data.eligibility_criteria,
        description=data.description,
        application_deadline=data.application_deadline,
        status=data.status,
        source_type=data.source_type,
    )
    db.add(drive)
    
    if commit:
        try:
            db.commit()
            db.refresh(drive)
        except IntegrityError as e:
            db.rollback()
            err_str = str(e.orig).lower()
            if "unique" in err_str or "fingerprint" in err_str:
                raise DuplicateDriveError(
                    f"Duplicate drive detected for {data.company_name} - {data.role} ({data.placement_season})"
                )
            raise
    else:
        try:
            db.flush()
        except IntegrityError as e:
            db.rollback()
            err_str = str(e.orig).lower()
            if "unique" in err_str or "fingerprint" in err_str:
                raise DuplicateDriveError(
                    f"Duplicate drive detected for {data.company_name} - {data.role} ({data.placement_season})"
                )
            raise

    logger.info("Drive created: id=%s company=%r role=%r season=%r", drive.id, drive.company_name, drive.role, drive.placement_season)
    return drive


def get_drive(db: Session, drive_id: uuid.UUID) -> Optional[Drive]:
    """
    Retrieve a Placement Drive by its integer primary key.

    Returns None if the drive does not exist.

    Args:
        db:       Active SQLAlchemy session.
        drive_id: UUID PK of the Drive.

    Returns:
        Drive ORM object or None.
    """
    return db.query(Drive).filter(Drive.id == drive_id).first()


def list_drives(
    db: Session,
    status: Optional[DriveStatus] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Drive]:
    """
    List Placement Drives with optional status filtering and pagination.

    Args:
        db:     Active SQLAlchemy session.
        status: Optional DriveStatus filter.
        skip:   Number of records to skip (offset).
        limit:  Maximum number of records to return.

    Returns:
        List of Drive ORM objects ordered by created_at DESC.
    """
    query = db.query(Drive)
    if status is not None:
        query = query.filter(Drive.status == status)
    return (
        query.order_by(Drive.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_drive(
    db: Session,
    drive: Drive,
    data: DriveUpdateRequest,
) -> Drive:
    """
    Partially update a Placement Drive.

    Only fields explicitly provided in `data` are updated. None values are
    skipped (partial update semantics, mirrors PUT vs PATCH convention).

    Args:
        db:    Active SQLAlchemy session.
        drive: The Drive ORM object to update (already fetched by get_drive).
        data:  Validated DriveUpdateRequest payload.

    Returns:
        The updated Drive ORM object after commit.
    """
    update_data = data.model_dump(exclude_none=True)
    
    # State transition guard
    new_status = update_data.get('status')
    if new_status and new_status != drive.status:
        allowed = VALID_TRANSITIONS.get(drive.status, set())
        if new_status not in allowed:
            raise ValueError(f"Invalid state transition from {drive.status.value} to {new_status.value}")
    
    new_company = update_data.get('company_name', drive.company_name)
    new_role = update_data.get('role', drive.role)
    new_season = update_data.get('placement_season', drive.placement_season)
    
    if 'company_name' in update_data or 'role' in update_data or 'placement_season' in update_data:
        update_data['drive_fingerprint'] = generate_drive_fingerprint(new_company, new_role, new_season)
    
    for field, value in update_data.items():
        setattr(drive, field, value)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        err_str = str(e.orig).lower()
        if "unique" in err_str or "fingerprint" in err_str:
            raise DuplicateDriveError(
                f"Update creates a duplicate drive for {new_company} - {new_role} ({new_season})"
            )
        raise

    db.refresh(drive)
    logger.info("Drive updated: id=%s fields=%s", drive.id, list(update_data.keys()))
    return drive


# ---------------------------------------------------------------------------
# Orchestration Foundation (Phase 4.4)
# ---------------------------------------------------------------------------

def create_drive_with_jd(
    db: Session, 
    data: DriveCreateRequest, 
    jd_text: Optional[str] = None, 
    pdf_file: Optional[Any] = None
) -> tuple[Drive, Any]:
    """
    Creates a drive, ingests its source, and queues analysis in a single transactional flow.
    """
    from app.services.drive_ingestion_service import ingest_text_submission, ingest_pdf_upload
    from app.services.drive_analysis_service import create_analysis_record
    
    # 1. Create drive without committing yet
    drive = create_drive(db, data, commit=False)
    
    try:
        # 2. Ingest Source (commits internally on success)
        if jd_text:
            ingest_text_submission(db, drive, jd_text)
        elif pdf_file:
            ingest_pdf_upload(db, drive, pdf_file)
        else:
            raise ValueError("Job description is required.")
            
        # 3. Queue Analysis
        analysis = create_analysis_record(db, drive.id)
        
        # update drive status to analyzing
        drive.status = DriveStatus.analyzing
        db.commit()
        db.refresh(drive)
        
        return drive, analysis
    except Exception as e:
        # If ingestion fails, ensure no dangling drive record remains
        db.rollback()
        raise

# ---------------------------------------------------------------------------
# Drive Snapshot — Storage Foundation (Phase 4.1)
# ---------------------------------------------------------------------------


def save_drive_snapshot(
    db: Session,
    drive_id: uuid.UUID,
    intelligence_payload: dict,
    snapshot_version: str,
    analysis_version: str,
    metadata_payload: Optional[dict] = None,
) -> DriveSnapshotModel:
    """
    Persist a Drive Intelligence snapshot.

    Phase 4.1: This function establishes the persistence contract. In Phase 4.1
    it will not be called by any production pipeline since no intelligence
    generation exists yet.

    Phase 4.3+ will invoke this after every successful intelligence pipeline run.

    Snapshot Strategy:
        - Immutable: snapshots are never updated, only appended.
        - Append-only: a new snapshot row is created per pipeline run.
        - Latest retrieval: use get_latest_drive_snapshot() — orders by created_at DESC.

    Does NOT commit — transaction is owned by the calling pipeline stage.
    (Mirrors analysis_persistence_service.save_snapshot() contract.)

    Args:
        db:                   Active SQLAlchemy session.
        drive_id:             UUID PK of the source Drive.
        intelligence_payload: Serialized DriveIntelligenceProfile dict.
        snapshot_version:     Schema version string (e.g. "1.0").
        analysis_version:     Pipeline version string (e.g. "4.3.0").
        metadata_payload:     Optional pipeline metadata dict.

    Returns:
        The DriveSnapshotModel ORM object (not yet committed).
    """
    snapshot = DriveSnapshotModel(
        drive_id=drive_id,
        snapshot_version=snapshot_version,
        analysis_version=analysis_version,
        intelligence_payload=intelligence_payload,
        metadata_payload=metadata_payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(snapshot)
    logger.info(
        "Queued DriveSnapshot for drive_id=%s version=%s",
        drive_id,
        snapshot_version,
    )
    return snapshot


def get_latest_drive_snapshot(
    db: Session,
    drive_id: uuid.UUID,
) -> Optional[DriveSnapshotModel]:
    """
    Retrieve the latest Drive Intelligence Snapshot for a given drive.

    Uses the composite index (drive_id, created_at DESC) for efficient lookup.
    Returns None if no snapshot exists yet (expected in Phase 4.1).

    Args:
        db:       Active SQLAlchemy session.
        drive_id: UUID PK of the Drive.

    Returns:
        DriveSnapshotModel or None.
    """
    return (
        db.query(DriveSnapshotModel)
        .filter(DriveSnapshotModel.drive_id == drive_id)
        .order_by(DriveSnapshotModel.created_at.desc())
        .first()
    )
