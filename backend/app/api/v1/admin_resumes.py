"""
app/api/v1/admin_resumes.py
-----------------------------
Phase 3.13 Admin CV Analysis API — all endpoints under /api/v1/admin/resumes.

Endpoints:
    GET  /api/v1/admin/resumes/queue-summary          — Status counts across all resumes
    GET  /api/v1/admin/resumes/pending                — Resumes awaiting processing
    GET  /api/v1/admin/resumes/{resume_id}/status     — Single resume processing status
    POST /api/v1/admin/resumes/{resume_id}/analyze    — Trigger analysis (async, 202)
    POST /api/v1/admin/resumes/analyze-batch          — Batch trigger (async, 202)

Security:
    - All endpoints require UserRole.admin via require_roles().
    - Admin has unrestricted visibility across all students' resumes — this is
      intentional by design.
    - Atomic state machine enforcement prevents duplicate pipeline triggers.
    - Race condition protection via DB-level compare-and-swap UPDATE.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.enums import ProcessingStatus, UserRole
from app.models.resume_file import ResumeFile
from app.models.user import User
from app.schemas.resume_analysis import (
    AdminResumeStatusResponse,
    AnalyzeTriggerResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    PendingQueueResponse,
    PendingResumeItem,
    QueueSummaryResponse,
)
from app.services import resume_service
from app.services.analysis_persistence_service import get_latest_snapshot
from fastapi import HTTPException

router = APIRouter(prefix="/api/v1/admin/resumes", tags=["Admin — Resume Processing"])


# ---------------------------------------------------------------------------
# Queue Summary
# ---------------------------------------------------------------------------


@router.get(
    "/queue-summary",
    response_model=QueueSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Queue summary",
    description="Returns the count of resumes in each processing state.",
)
def queue_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> QueueSummaryResponse:
    counts = resume_service.get_queue_summary(db)
    return QueueSummaryResponse(**counts)


# ---------------------------------------------------------------------------
# Pending Queue
# ---------------------------------------------------------------------------


@router.get(
    "/pending",
    response_model=PendingQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="List pending resumes",
    description=(
        "Returns all resumes with status 'uploaded' or 'failed' — i.e. those "
        "awaiting admin-triggered processing. Ordered oldest-first."
    ),
)
def pending_resumes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> PendingQueueResponse:
    items_raw = resume_service.get_pending_resumes(db, skip=skip, limit=limit)
    items = [PendingResumeItem(**row) for row in items_raw]
    return PendingQueueResponse(items=items, total=len(items))


# ---------------------------------------------------------------------------
# Single Resume Status
# ---------------------------------------------------------------------------


@router.get(
    "/{resume_id}/status",
    response_model=AdminResumeStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get resume processing status",
    description="Returns detailed processing and analysis status for any resume.",
)
def resume_status(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> AdminResumeStatusResponse:
    resume = resume_service.get_admin_resume_status(db, resume_id)

    # Load snapshot for analysis_status and generated_at (Phase 3.13B)
    snapshot = get_latest_snapshot(db, resume_id)

    return AdminResumeStatusResponse(
        resume_id=resume.id,
        student_id=resume.student_id,
        resume_type=resume.resume_type,
        processing_status=resume.processing_status,
        analysis_status="completed" if snapshot else None,
        analyzed_at=snapshot.generated_at if snapshot else None,
        last_updated=resume.updated_at,
    )


# ---------------------------------------------------------------------------
# Trigger Single Analysis
# ---------------------------------------------------------------------------


@router.post(
    "/{resume_id}/analyze",
    response_model=AnalyzeTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger resume analysis",
    description=(
        "Enqueues the full CV analysis pipeline for a single resume. "
        "Returns 202 Accepted immediately — analysis runs asynchronously. "
        "Use ?force=true to reprocess a resume that is already completed. "
        "Returns 409 Conflict if already processing or status is not triggerable."
    ),
)
def trigger_analysis(
    resume_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Set to true to reprocess a completed resume."),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> AnalyzeTriggerResponse:
    resume = resume_service.trigger_resume_analysis(
        db, resume_id, background_tasks, force=force
    )
    return AnalyzeTriggerResponse(
        resume_id=resume.id,
        status="queued",
        message=f"Analysis pipeline queued for {resume.resume_type.value} resume.",
    )


# ---------------------------------------------------------------------------
# Batch Analysis
# ---------------------------------------------------------------------------


@router.post(
    "/analyze-batch",
    response_model=BatchAnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch trigger resume analysis",
    description=(
        "Enqueues the analysis pipeline for multiple resumes. "
        "Provide either `resume_ids` (explicit list) or `limit` (auto-select oldest pending). "
        "Maximum limit is 50. Skips resumes already processing."
    ),
)
def trigger_batch_analysis(
    request: BatchAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> BatchAnalyzeResponse:
    # Validate that at least one of resume_ids or limit is provided
    if not request.resume_ids and request.limit is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either resume_ids or limit must be provided.",
        )

    queued: list[uuid.UUID] = []
    skipped: list[uuid.UUID] = []
    reasons: dict[str, str] = {}

    if request.resume_ids:
        # Explicit list: attempt to trigger each one
        target_ids = request.resume_ids
    else:
        # Auto-select: oldest uploaded/failed resumes up to limit
        rows = resume_service.get_pending_resumes(db, skip=0, limit=request.limit)
        target_ids = [row["resume_id"] for row in rows]

    for rid in target_ids:
        try:
            resume_service.trigger_resume_analysis(db, rid, background_tasks, force=False)
            queued.append(rid)
        except HTTPException as exc:
            skipped.append(rid)
            reasons[str(rid)] = exc.detail

    return BatchAnalyzeResponse(
        queued=queued,
        skipped=skipped,
        reasons=reasons,
        total_queued=len(queued),
        total_skipped=len(skipped),
    )
