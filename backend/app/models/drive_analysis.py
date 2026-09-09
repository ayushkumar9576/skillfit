"""
app/models/drive_analysis.py
------------------------------
DriveAnalysis ORM model — Phase 4.3 Drive Intelligence Engine.

Purpose:
    Track every Drive Intelligence Engine execution run. Acts as the audit
    trail between DriveSource (what we ingested) and DriveSnapshot (what we
    understood). A new DriveAnalysis row is created for every analysis attempt,
    including failed attempts.

Lifecycle:
    PENDING   → Analysis record created; engine not yet started.
    RUNNING   → Intelligence Engine is actively processing.
    COMPLETED → Engine succeeded; associated DriveSnapshot has been created.
    FAILED    → Engine or Governance Layer raised an unrecoverable error;
                no snapshot was created. error_message captures the reason.

Relationship to other models:
    Drive (1) ──< DriveAnalysis (M)
    DriveSource (1) ──< DriveAnalysis (M)   [the exact source analyzed]
    DriveAnalysis (1) ──< DriveSnapshot (1) [optional; null until completed]

Immutability:
    DriveAnalysis rows record the final terminal state. After reaching
    COMPLETED or FAILED, no fields are updated. Subsequent runs create
    new DriveAnalysis rows (append-only audit log).

Cost & quality tracking:
    processing_metadata (JSONB) carries:
        token_usage:              {input_tokens, output_tokens, total_tokens}
        estimated_cost:           float (USD, approximated from provider pricing)
        quality_score:            float 0.0–1.0 (post-governance quality)
        evidence_coverage:        float 0.0–1.0 (% artifacts with explicit evidence)
        confidence_distribution:  {HIGH: N, MEDIUM: N, LOW: N}
        validation_warnings:      int (count of recoverable auto-corrections)
        governance_corrections:   list of correction descriptions
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.schema import Index

from app.core.enums import DriveAnalysisStatus
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.drive import Drive
    from app.models.drive_source import DriveSource
    from app.models.drive_snapshot import DriveSnapshotModel


class DriveAnalysis(Base):
    """
    Execution record for a single Drive Intelligence Engine run.

    One row per analysis attempt. All attempts — including failures — are
    persisted to provide a complete audit trail of intelligence generation.
    """

    __tablename__ = "drive_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # -----------------------------------------------------------------------
    # Foreign keys
    # -----------------------------------------------------------------------

    drive_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drives.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drive_sources.id", ondelete="SET NULL"),
        nullable=True,  # Nullable so the record survives source deletion
        index=True,
    )
    # Populated only after COMPLETED — links to the snapshot this run produced
    snapshot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drive_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # -----------------------------------------------------------------------
    # Status & lifecycle timestamps
    # -----------------------------------------------------------------------

    status = Column(
        String(20),
        nullable=False,
        default=DriveAnalysisStatus.pending.value,
        server_default=DriveAnalysisStatus.pending.value,
        index=True,
    )

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # -----------------------------------------------------------------------
    # Versioning & provenance
    # -----------------------------------------------------------------------

    # e.g. "4.3.0" — which code version of the engine produced this
    analysis_version = Column(String(20), nullable=False)

    # e.g. "v1" — which prompt template was used
    prompt_version = Column(String(20), nullable=False)

    # e.g. "gemini-1.5-pro" — exact LLM model used
    model_name = Column(String(100), nullable=False)

    # -----------------------------------------------------------------------
    # Failure tracking
    # -----------------------------------------------------------------------

    error_message = Column(Text, nullable=True)

    # -----------------------------------------------------------------------
    # Cost & quality metadata (JSONB)
    # Structure:
    # {
    #   "token_usage": {"input_tokens": N, "output_tokens": N, "total_tokens": N},
    #   "estimated_cost": 0.001234,
    #   "quality_score": 0.92,
    #   "evidence_coverage": 0.87,
    #   "confidence_distribution": {"HIGH": 5, "MEDIUM": 3, "LOW": 1},
    #   "validation_warnings": 2,
    #   "governance_corrections": ["Merged duplicate technology: Python", ...]
    # }
    # -----------------------------------------------------------------------

    processing_metadata = Column(JSONB, nullable=True, default=dict)

    # -----------------------------------------------------------------------
    # Relationships
    # -----------------------------------------------------------------------

    drive: Mapped["Drive"] = relationship("Drive", back_populates="drive_analyses")

    source: Mapped[Optional["DriveSource"]] = relationship(
        "DriveSource", foreign_keys=[source_id]
    )

    snapshot: Mapped[Optional["DriveSnapshotModel"]] = relationship(
        "DriveSnapshotModel",
        foreign_keys="DriveSnapshotModel.analysis_id",
        back_populates="analysis",
        uselist=False,
    )

    # -----------------------------------------------------------------------
    # Indexes
    # -----------------------------------------------------------------------

    __table_args__ = (
        # Composite index for the most common query: latest analyses for a drive
        Index(
            "ix_drive_analyses_drive_created",
            "drive_id",
            "created_at",
        ),
    )


    def __repr__(self) -> str:
        return (
            f"<DriveAnalysis id={self.id} drive_id={self.drive_id} "
            f"status={self.status} model={self.model_name}>"
        )
