"""
app/services/analysis_persistence_service.py
--------------------------------------------
Phase 3.13B — Snapshot-Only Analysis Persistence Service.

Single responsibility: persist CandidateIntelligenceProfile snapshots into the
candidate_intelligence_snapshots table and retrieve them.

Design contracts:
    - This service NEVER calls db.commit() or db.rollback().
    - It calls db.add() only.
    - Transaction ownership stays with the pipeline's _set_status(completed)
      call, which commits everything atomically after Stage 8 returns True.
    - Failures are logged and propagated — never silently swallowed at this level.

Snapshot architecture:
    One resume may have many snapshots.
    Latest snapshot is determined by generated_at DESC (composite index).
    No unique constraint on resume_id — historical runs are preserved.
    profile_version = schema version of CandidateIntelligenceProfile (e.g. "1.0")
    analysis_version = version of the pipeline that produced it (e.g. "4.0.0")
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.analysis.models.candidate_profile import CandidateIntelligenceProfile
from app.analysis.serialization.profile_serializer import ProfileSerializer
from app.models.candidate_intelligence_snapshot import CandidateIntelligenceSnapshotModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API — Snapshots
# ---------------------------------------------------------------------------


def save_snapshot(
    db: Session,
    profile: CandidateIntelligenceProfile,
    resume_id: uuid.UUID,
) -> CandidateIntelligenceSnapshotModel:
    """
    Serialize and persist a CandidateIntelligenceProfile snapshot.

    Does NOT commit — transaction is owned by the calling pipeline stage.
    """
    payload = ProfileSerializer.to_snapshot_payload(profile)
    snapshot = CandidateIntelligenceSnapshotModel(
        resume_id=resume_id,
        profile_version=payload["schema_version"],
        analysis_version=payload["analysis_version"],
        generated_at=datetime.now(timezone.utc),
        profile_json=payload,
    )
    db.add(snapshot)
    logger.info("Queued CandidateIntelligenceSnapshot for resume_id=%s", resume_id)
    return snapshot


def get_latest_snapshot(
    db: Session,
    resume_id: uuid.UUID,
) -> Optional[CandidateIntelligenceSnapshotModel]:
    """
    Retrieve the latest CandidateIntelligenceSnapshot for a given resume.

    Uses the composite index (resume_id, generated_at DESC) for efficient lookup.
    Returns None if no snapshot exists yet.
    """
    return (
        db.query(CandidateIntelligenceSnapshotModel)
        .filter(CandidateIntelligenceSnapshotModel.resume_id == resume_id)
        .order_by(CandidateIntelligenceSnapshotModel.generated_at.desc())
        .first()
    )


def get_profile(
    db: Session,
    resume_id: uuid.UUID,
) -> Optional[CandidateIntelligenceProfile]:
    """
    Retrieve and deserialize the latest CandidateIntelligenceProfile for a resume.

    Returns None if no snapshot exists or deserialization fails.
    Errors during deserialization are logged and suppressed — callers should
    handle None gracefully.
    """
    snapshot = get_latest_snapshot(db, resume_id)
    if not snapshot:
        return None
    try:
        return ProfileSerializer.from_snapshot_payload(snapshot.profile_json)
    except Exception as exc:
        logger.error(
            "Failed to deserialize snapshot for resume_id=%s: %s",
            resume_id,
            exc,
        )
        return None


# ---------------------------------------------------------------------------
# Public API — Pipeline Entry Point
# ---------------------------------------------------------------------------


def persist_analysis_results(
    db: Session,
    student_id: int,
    resume_id: uuid.UUID,
    intelligence_profile: Optional[CandidateIntelligenceProfile] = None,
    # Legacy parameters kept for signature compatibility — ignored
    project_result=None,
    internship_result=None,
    certification_result=None,
    skill_result=None,
    readiness_result=None,
) -> bool:
    """
    Persist analysis results as a CandidateIntelligenceSnapshot.

    Phase 3.13B: Snapshot-only. All legacy write paths have been removed.
    The legacy parameters (project_result, internship_result, etc.) are retained
    in the signature only for call-site compatibility during transition.
    They are NOT written to any table.

    Transaction contract:
        - Does NOT commit or rollback.
        - Calls db.add() only via save_snapshot().
        - The pipeline's _set_status(completed) commit at Stage 8 atomically
          persists the snapshot alongside the status update.

    Args:
        db:                  Active SQLAlchemy session (no autocommit).
        student_id:          Integer PK of the Student record (logged only).
        resume_id:           UUID PK of the ResumeFile record.
        intelligence_profile: The CandidateIntelligenceProfile to snapshot.

    Returns:
        True on success. False if snapshotting fails.
    """
    if not intelligence_profile:
        logger.warning(
            "persist_analysis_results called with no intelligence_profile "
            "for student_id=%s resume_id=%s — no snapshot written.",
            student_id,
            resume_id,
        )
        return True  # Not a hard failure — pipeline may have skipped aggregation

    try:
        save_snapshot(db, intelligence_profile, resume_id)
        db.flush()
        logger.info(
            "Snapshot persistence flush successful: student_id=%s resume_id=%s",
            student_id,
            resume_id,
        )
        return True

    except Exception as exc:
        logger.error(
            "Snapshot persistence FAILED for student_id=%s resume_id=%s: %s",
            student_id,
            resume_id,
            exc,
            exc_info=True,
        )
        return False
