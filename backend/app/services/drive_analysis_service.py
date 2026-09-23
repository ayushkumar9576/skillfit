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
from app.core.enums import DriveAnalysisStatus, DriveStatus
from app.drives.parsers.contract import ParsedDriveContent
from app.models.drive import Drive
from app.models.drive_analysis import DriveAnalysis
from app.models.drive_snapshot import DriveSnapshotModel
from app.models.drive_source import DriveSource
from app.services.llm.exceptions import LLMError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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


def _get_drive_or_404(db: Session, drive_id: uuid.UUID) -> Drive:
    drive = db.get(Drive, drive_id)
    if drive is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Drive {drive_id} not found.")
    return drive


def _get_latest_source_or_404(db: Session, drive_id: uuid.UUID) -> DriveSource:
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
    drive_id: uuid.UUID,
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
        "DriveAnalysis PENDING | analysis_id=%s drive_id=%s source_version=%d",
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
    import time
    t0 = time.perf_counter()
    drive = db.query(Drive).filter(Drive.id == analysis.drive_id).first()
    
    print(
        "\033[96m\n================================================================================\n"
        "🚀 DRIVE ANALYSIS PIPELINE\n"
        "================================================================================\n"
        f"Analysis ID : {analysis_id}\n"
        f"Company     : {drive.company_name}\n"
        f"Role        : {drive.role}\n"
        "================================================================================\n\033[0m"
    )

    print("\033[96m################################################################################")
    print("# STEP 1/5 - INITIALIZING INTELLIGENCE PIPELINE")
    print("################################################################################\n\033[0m")
    
    analysis.status = DriveAnalysisStatus.running.value
    analysis.started_at = datetime.now(timezone.utc)
    db.commit()

    source = db.query(DriveSource).filter(DriveSource.id == analysis.source_id).first()
    
    t1 = time.perf_counter()
    print("\033[96m\n################################################################################")
    print("# STEP 1/5 COMPLETED ✓")
    print("################################################################################\n\033[0m")
    
    print("\033[96m################################################################################")
    print("# STEP 2/5 - NORMALIZING JOB DESCRIPTION")
    print("################################################################################\n\033[0m")
    
    _engine = engine or DriveIntelligenceEngine(prompt_version=analysis.prompt_version)
    content = _reconstruct_parsed_content(source)
    
    t2 = time.perf_counter()
    print("\033[96m\n################################################################################")
    print("# STEP 2/5 COMPLETED ✓")
    print("################################################################################\n\033[0m")

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
        
        if drive.status == DriveStatus.analyzing:
            drive.status = DriveStatus.analysis_failed
            
        db.commit()
        print(f"\033[91mDriveAnalysis FAILED | GovernanceValidationError | analysis_id={analysis_id}\nError: {exc}\033[0m")
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
        
        if drive.status == DriveStatus.analyzing:
            drive.status = DriveStatus.analysis_failed
            
        db.commit()
        print(f"\033[91mDriveAnalysis FAILED | EngineError | analysis_id={analysis_id}\nError: {exc}\033[0m")
        logger.error("DriveAnalysis FAILED | EngineError | analysis_id=%s", analysis_id, exc_info=True)
        return analysis

    t4 = time.perf_counter()
    # --- Build and persist snapshot ---
    print("\033[96m################################################################################")
    print("# STEP 5/5 - FINALIZING ANALYSIS SNAPSHOT")
    print("################################################################################\n\033[0m")
    
    try:
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
        db.flush()  # Force INSERT to avoid FK violation when updating drive_analyses
        
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
        
        if drive.status == DriveStatus.analyzing:
            drive.status = DriveStatus.ready

        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"\033[91mDriveAnalysis FAILED | Database Finalization Error | analysis_id={analysis_id}\nError: {exc}\033[0m")
        logger.error("DriveAnalysis FAILED | Database Finalization Error | analysis_id=%s", analysis_id, exc_info=True)
        
        # Re-fetch models after rollback to update their failure states safely
        analysis = db.query(DriveAnalysis).filter(DriveAnalysis.id == analysis_id).first()
        drive = db.query(Drive).filter(Drive.id == analysis.drive_id).first()
        
        if analysis:
            analysis.status = DriveAnalysisStatus.failed.value
            analysis.failed_at = datetime.now(timezone.utc)
            analysis.error_message = f"Database finalization error: {str(exc)}"
            meta = analysis.processing_metadata or {}
            analysis.processing_metadata = {**meta, "failure_reason": "DB_COMMIT_ERROR", "validation_stage": "finalization"}
            
        if drive and drive.status == DriveStatus.analyzing:
            drive.status = DriveStatus.analysis_failed
            
        db.commit()
        return analysis

    t5 = time.perf_counter()

    print("\033[96m\n################################################################################")
    print("# STEP 5/5 COMPLETED ✓")
    print("################################################################################\n\033[0m")

    print(
        "\033[96m\n################################################################################\n"
        "# DRIVE ANALYSIS COMPLETED ✓\n"
        "################################################################################\n\n"
        f"Analysis ID : {analysis.id}\n"
        f"Company     : {drive.company_name}\n"
        f"Role        : {drive.role}\n\n"
        f"Step 1 : {t1 - t0:.2f}s\n"
        f"Step 2 : {t2 - t1:.2f}s\n"
        f"Step 3 : {result.timing_stats['step3']:.2f}s\n"
        f"Step 4 : {result.timing_stats['step4']:.2f}s\n"
        f"Step 5 : {t5 - t4:.2f}s\n\n"
        f"Total  : {t5 - t0:.2f}s\n\n"
        "################################################################################\n\033[0m"
    )

    return analysis


def get_analysis_history(
    db: Session,
    drive_id: uuid.UUID,
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
    drive_id: uuid.UUID,
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
    drive_id: uuid.UUID,
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
