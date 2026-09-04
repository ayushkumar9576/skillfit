"""
app/api/v1/drives.py
---------------------
Phase 4.1 — Placement Drive Intelligence Foundation API.

Endpoints:
    POST   /api/v1/drives              Create a Placement Drive
    GET    /api/v1/drives              List Placement Drives
    GET    /api/v1/drives/{id}         Get a single Placement Drive
    PATCH  /api/v1/drives/{id}         Partially update a Drive
    GET    /api/v1/drives/{id}/snapshot Get the latest Drive Intelligence Snapshot

Phase 4.1 scope:
    - Drive CRUD only.
    - Snapshot endpoint exists but returns 404 until Phase 4.3 generates snapshots.

Deferred to later phases:
    - POST /api/v1/drives/{id}/analyze  (Phase 4.3 — intelligence pipeline trigger)
    - GET  /api/v1/drives/{id}/analysis (Phase 4.3 — analysis tracking)

Auth:
    - Drive creation and updates require admin role.
    - Drive retrieval is open to authenticated users.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.enums import DriveStatus, UserRole
from app.models.user import User
from app.schemas.drive_schemas import (
    DriveCreateRequest,
    DriveListResponse,
    DriveResponse,
    DriveSnapshotResponse,
    DriveUpdateRequest,
)
from app.services import drive_service

router = APIRouter(prefix="/api/v1/drives", tags=["Drives"])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Partial Update
# ---------------------------------------------------------------------------


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
# Snapshot Retrieval — Phase 4.1 Foundation
# ---------------------------------------------------------------------------


@router.get("/{drive_id}/snapshot", response_model=DriveSnapshotResponse)
def get_drive_snapshot(
    drive_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.faculty)),
):
    """
    Retrieve the latest Drive Intelligence Snapshot for a given drive.

    Phase 4.1: This endpoint is defined as part of the foundation API but will
    return 404 until Phase 4.3 populates snapshots via intelligence generation.

    Phase 4.3 will introduce POST /api/v1/drives/{id}/analyze which triggers
    the intelligence pipeline and creates the first snapshot.
    """
    # Verify drive exists first
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
