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

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.enums import DriveStatus, DriveSourceType
from app.models.drive import Drive
from app.models.drive_snapshot import DriveSnapshotModel
from app.schemas.drive_schemas import DriveCreateRequest, DriveUpdateRequest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Drive CRUD
# ---------------------------------------------------------------------------


def create_drive(db: Session, data: DriveCreateRequest) -> Drive:
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
    drive = Drive(
        company_name=data.company_name,
        role=data.role,
        job_type=data.job_type,
        location=data.location,
        package=data.package,
        eligibility_criteria=data.eligibility_criteria,
        description=data.description,
        application_deadline=data.application_deadline,
        required_skills=data.required_skills or [],
        preferred_skills=data.preferred_skills or [],
        structured_eligibility=data.structured_eligibility or {},
        status=data.status,
        source_type=data.source_type,
    )
    db.add(drive)
    db.commit()
    db.refresh(drive)
    logger.info("Drive created: id=%s company=%r role=%r", drive.id, drive.company_name, drive.role)
    return drive


def get_drive(db: Session, drive_id: int) -> Optional[Drive]:
    """
    Retrieve a Placement Drive by its integer primary key.

    Returns None if the drive does not exist.

    Args:
        db:       Active SQLAlchemy session.
        drive_id: Integer PK of the Drive.

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
    for field, value in update_data.items():
        setattr(drive, field, value)

    db.commit()
    db.refresh(drive)
    logger.info("Drive updated: id=%s fields=%s", drive.id, list(update_data.keys()))
    return drive


# ---------------------------------------------------------------------------
# Drive Snapshot — Storage Foundation (Phase 4.1)
# ---------------------------------------------------------------------------


def save_drive_snapshot(
    db: Session,
    drive_id: int,
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
        drive_id:             Integer PK of the source Drive.
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
    drive_id: int,
) -> Optional[DriveSnapshotModel]:
    """
    Retrieve the latest Drive Intelligence Snapshot for a given drive.

    Uses the composite index (drive_id, created_at DESC) for efficient lookup.
    Returns None if no snapshot exists yet (expected in Phase 4.1).

    Args:
        db:       Active SQLAlchemy session.
        drive_id: Integer PK of the Drive.

    Returns:
        DriveSnapshotModel or None.
    """
    return (
        db.query(DriveSnapshotModel)
        .filter(DriveSnapshotModel.drive_id == drive_id)
        .order_by(DriveSnapshotModel.created_at.desc())
        .first()
    )
