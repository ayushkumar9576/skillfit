"""
app/services/drive_analysis_service.py
----------------------------------------
Drive Analysis Service — Phase 4.3 Drive Intelligence Engine.

Responsibilities:
    - Manage the DriveAnalysis state machine (PENDING → RUNNING → COMPLETED/FAILED).
    - Orchestrate the full analysis pipeline:
          DriveSource → ParsedDriveContent → DriveIntelligenceEngine → DriveSnapshot
    - Create immutable DriveSnapshot records on success.
    - Persist failure metadata on analysis errors (no snapshot created).
    - Provide query helpers for history and latest snapshot.

Architecture:
    Follows the flat API → Service → SQLAlchemy Session pattern established
    in Phase 4.2. No repository layer.

    API endpoint calls:
        create_and_run_analysis() for synchronous trigger.
        get_analysis_history()   for audit log retrieval.
        get_latest_snapshot()    for snapshot retrieval.
        get_snapshot_by_id()     for specific snapshot retrieval.

Source Boundary Rule (enforced here):
    The service only reads DriveSource rows — never raw files.
    ParsedDriveContent is reconstructed from DriveSource.normalized_content.

Snapshot Immutability:
    Every successful analysis appends a new DriveSnapshot row.
    Existing snapshots are never modified.

Cost tracking:
    Stores LLM token usage + quality metrics in DriveAnalysis.processing_metadata.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.analysis.drives.governance import GovernanceValidationError
from app.analysis.drives.schemas.intelligence import INTELLIGENCE_SCHEMA_VERSION
from app.analysis.drives.schemas.prompts import DEFAULT_PROMPT_VERSION
from app.analysis.engines.drive_intelligence_engine import (
    ANALYSIS_VERSION,
    DriveIntelligenceEngine,
)
from app.core.enums import DriveAnalysisStatus
from app.drives.parsers.contract import ParsedDriveContent
from app.models.drive import Drive
from app.models.drive_analysis import DriveAnalysis
from app.models.drive_snapshot import DriveSnapshotModel
from app.models.drive_source import DriveSource
from app.services.llm.exceptions import LLMError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Approximate cost per 1M tokens (USD). Update as provider pricing changes.
_COST_PER_1M_INPUT_TOKENS: float = float(
    os.getenv("LLM_COST_PER_1M_INPUT_TOKENS", "0.35")
)
_COST_PER_1M_OUTPUT_TOKENS: float = float(
    os.getenv("LLM_COST_PER_1M_OUTPUT_TOKENS", "1.05")
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_drive_or_404(db: Session, drive_id: int) -> Drive:
    drive = db.get(Drive, drive_id)
    if drive is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Drive {drive_id} not found.")
    return drive


def _get_latest_source_or_404(db: Session, drive_id: int) -> DriveSource:
    source = (
        db.query(DriveSource)
        .filter(DriveSource.drive_id == drive_id)
        .order_by(desc(DriveSource.version))
        .first()
    )
    if source is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"Drive {drive_id} has no ingested source. "
                   "Upload a job description first via POST /drives/{id}/upload.",
        )
    return source


def _reconstruct_parsed_content(source: DriveSource) -> ParsedDriveContent:
    """
    Reconstruct ParsedDriveContent from a persisted DriveSource row.

    This is the Source Boundary gate: intelligence generation only ever
    reads from DriveSource, never from raw files.
    """
    meta = source.processing_metadata or {}
    normalized = source.normalized_content or ""
    raw = source.raw_content or ""
    return ParsedDriveContent(
        contract_version="1.0",
        drive_id=source.drive_id,
        source_id=str(source.id),
        source_version=source.version,
        source_metadata=meta,
        raw_text=raw,
        normalized_text=normalized,
        statistics={
            "character_count": meta.get("character_count", len(normalized)),
            "word_count": meta.get("word_count", len(normalized.split())),
        },
        extractor_warnings=meta.get("extractor_warnings", []),
        normalizer_transformations=meta.get("transformations_applied", []),
        is_duplicate=meta.get("is_duplicate", False),
        duplicate_of_version=meta.get("duplicate_of_version"),
    )



def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens / 1_000_000 * _COST_PER_1M_INPUT_TOKENS
        + output_tokens / 1_000_000 * _COST_PER_1M_OUTPUT_TOKENS
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


def create_analysis_record(
    db: Session,
    drive_id: int,
    *,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> DriveAnalysis:
    """
    Synchronously create a PENDING DriveAnalysis record or return an existing one.

    Idempotency: Prevents spawning a duplicate analysis if a PENDING, RUNNING,
    or COMPLETED analysis already exists for the exact combination of:
    drive_id + source_id + prompt_version.
    """
    drive = _get_drive_or_404(db, drive_id)
    source = _get_latest_source_or_404(db, drive_id)

    # Idempotency check
    existing = (
        db.query(DriveAnalysis)
        .filter(
            DriveAnalysis.drive_id == drive_id,
            DriveAnalysis.source_id == source.id,
            DriveAnalysis.prompt_version == prompt_version,
            DriveAnalysis.status.in_([
                DriveAnalysisStatus.pending.value,
                DriveAnalysisStatus.running.value,
                DriveAnalysisStatus.completed.value,
            ]),
        )
        .first()
    )
    if existing:
        logger.info(
            "DriveAnalysis IDEMPOTENCY HIT | returning existing analysis_id=%s status=%s",
            existing.id,
            existing.status,
        )
        return existing

    # Create new PENDING record
    analysis = DriveAnalysis(
        id=uuid.uuid4(),
        drive_id=drive_id,
        source_id=source.id,
        status=DriveAnalysisStatus.pending.value,
        analysis_version=ANALYSIS_VERSION,
        prompt_version=prompt_version,
        model_name="",
        processing_metadata={},
    )
    db.add(analysis)
    db.flush()

    logger.info(
        "DriveAnalysis PENDING | analysis_id=%s drive_id=%d source_version=%d",
        analysis.id,
        drive_id,
        source.version,
    )
    return analysis


async def execute_analysis_background(
    db: Session,
    analysis_id: uuid.UUID,
    *,
    engine: Optional[DriveIntelligenceEngine] = None,
) -> DriveAnalysis:
    """
    Execute the intelligence pipeline for a PENDING analysis.

    Transitions to RUNNING, executes LLM + Governance, and finalizes to COMPLETED or FAILED.
    """
    analysis = db.query(DriveAnalysis).filter(DriveAnalysis.id == analysis_id).first()
    if not analysis or analysis.status != DriveAnalysisStatus.pending.value:
        logger.warning("execute_analysis_background aborted | analysis_id=%s not pending", analysis_id)
        return analysis

    # --- Transition to RUNNING ---
    analysis.status = DriveAnalysisStatus.running.value
    analysis.started_at = datetime.now(timezone.utc)
    db.commit()

    source = db.query(DriveSource).filter(DriveSource.id == analysis.source_id).first()
    drive = db.query(Drive).filter(Drive.id == analysis.drive_id).first()
    
    _engine = engine or DriveIntelligenceEngine(prompt_version=analysis.prompt_version)
    content = _reconstruct_parsed_content(source)

    try:
        result = await _engine.analyze(
            content=content,
            company_name=drive.company_name,
            role=drive.role,
        )
    except GovernanceValidationError as exc:
        # Expected governance validation failure
        analysis.status = DriveAnalysisStatus.failed.value
        analysis.failed_at = datetime.now(timezone.utc)
        analysis.error_message = str(exc)
        
        # In Phase 4.3A we add specific failure tracking
        meta = analysis.processing_metadata or {}
        # Ensure dict format is maintained via JSONB assignment
        new_meta = {**meta, "failure_reason": "GOVERNANCE_VALIDATION_ERROR", "validation_stage": "governance_layer"}
        analysis.processing_metadata = new_meta
        
        db.commit()
        logger.error("DriveAnalysis FAILED | GovernanceValidationError | analysis_id=%s", analysis_id)
        return analysis
    except (LLMError, Exception) as exc:
        # Unexpected infrastructure/LLM failure
        analysis.status = DriveAnalysisStatus.failed.value
        analysis.failed_at = datetime.now(timezone.utc)
        analysis.error_message = str(exc)
        
        meta = analysis.processing_metadata or {}
        new_meta = {**meta, "failure_reason": "ENGINE_ERROR", "validation_stage": "engine_execution"}
        analysis.processing_metadata = new_meta
        
        db.commit()
        logger.error("DriveAnalysis FAILED | EngineError | analysis_id=%s", analysis_id, exc_info=True)
        return analysis

    # --- Build and persist snapshot ---
    token_usage = result.token_usage
    estimated_cost = _estimate_cost(
        token_usage.get("input_tokens", 0),
        token_usage.get("output_tokens", 0),
    )
    governance_dict = result.governance_report.to_dict()

    snapshot = DriveSnapshotModel(
        id=uuid.uuid4(),
        drive_id=analysis.drive_id,
        source_id=analysis.source_id,
        analysis_id=analysis.id,
        snapshot_version=INTELLIGENCE_SCHEMA_VERSION,
        analysis_version=ANALYSIS_VERSION,
        prompt_version=result.prompt_version,
        model_name=result.model_name,
        intelligence_schema_version=INTELLIGENCE_SCHEMA_VERSION,
        intelligence_payload=result.profile.to_snapshot_dict(),
        metadata_payload={
            "raw_llm_output_length": len(result.raw_llm_output),
        },
    )
    db.add(snapshot)
    
    # --- Update analysis to COMPLETED ---
    analysis.status = DriveAnalysisStatus.completed.value
    analysis.completed_at = datetime.now(timezone.utc)
    analysis.model_name = result.model_name
    analysis.snapshot_id = snapshot.id
    
    meta = analysis.processing_metadata or {}
    new_meta = {
        **meta,
        "token_usage": token_usage,
        "estimated_cost": round(estimated_cost, 6),
        **governance_dict,
    }
    analysis.processing_metadata = new_meta

    db.commit()

    logger.info(
        "DriveAnalysis COMPLETED | analysis_id=%s snapshot_id=%s",
        analysis.id,
        snapshot.id,
    )
    return analysis


def get_analysis_history(
    db: Session,
    drive_id: int,
    *,
    limit: int = 20,
) -> List[DriveAnalysis]:
    """
    Return historical DriveAnalysis records for a drive, newest first.

    Args:
        db:       Active SQLAlchemy session.
        drive_id: Target drive.
        limit:    Maximum number of records to return.

    Returns:
        List of DriveAnalysis records, ordered by created_at DESC.
    """
    return (
        db.query(DriveAnalysis)
        .filter(DriveAnalysis.drive_id == drive_id)
        .order_by(desc(DriveAnalysis.created_at))
        .limit(limit)
        .all()
    )


def get_latest_snapshot(
    db: Session,
    drive_id: int,
) -> Optional[DriveSnapshotModel]:
    """
    Return the most recently created DriveSnapshot for a drive.

    Uses created_at DESC ordering — never assumes ID ordering is reliable.

    Returns:
        The latest DriveSnapshotModel, or None if no snapshots exist.
    """
    return (
        db.query(DriveSnapshotModel)
        .filter(DriveSnapshotModel.drive_id == drive_id)
        .order_by(desc(DriveSnapshotModel.created_at))
        .first()
    )


def get_snapshot_by_id(
    db: Session,
    drive_id: int,
    snapshot_id: str,
) -> Optional[DriveSnapshotModel]:
    """
    Return a specific DriveSnapshot by ID.

    Args:
        db:          Active SQLAlchemy session.
        drive_id:    Drive the snapshot belongs to (for ownership validation).
        snapshot_id: UUID string of the snapshot.

    Returns:
        DriveSnapshotModel or None.
    """
    try:
        sid = uuid.UUID(snapshot_id)
    except ValueError:
        return None

    return (
        db.query(DriveSnapshotModel)
        .filter(
            DriveSnapshotModel.id == sid,
            DriveSnapshotModel.drive_id == drive_id,
        )
        .first()
    )
