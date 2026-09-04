"""
app/models/drive_snapshot.py
------------------------------
Stores versioned JSONB snapshots of the DriveIntelligenceProfile.

Phase 4.1 — Initial model (storage foundation only).

Design:
    Mirrors CandidateIntelligenceSnapshotModel on the Drive side.
    Snapshots are immutable point-in-time records — never updated.
    Every new analysis run appends a new row; history is preserved.
    The latest snapshot for a drive is determined by created_at DESC.

Snapshot Creation Strategy:
    Phase 4.1  — Table exists; NO rows are created yet. There is no
                  intelligence generation engine.
    Phase 4.3+ — A snapshot row is created after every successful execution
                  of the Drive Intelligence Analysis pipeline.

Naming symmetry with Candidate side:
    CandidateIntelligenceSnapshotModel  →  DriveSnapshotModel
    profile_version / analysis_version  →  snapshot_version / analysis_version
    profile_json                        →  intelligence_payload
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.schema import Index

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.drive import Drive
    from app.models.drive_analysis import DriveAnalysis
    from app.models.drive_source import DriveSource


class DriveSnapshotModel(Base):
    """
    ORM model for versioned Drive Intelligence snapshots.

    Each row stores the serialized DriveIntelligenceProfile produced by a
    single pipeline execution. Multiple snapshots may exist for the same
    drive as the intelligence is refined over time.

    Attributes:
        id:                  UUID primary key.
        drive_id:            FK to drives.id — cascade deletes clean up snapshots.
        snapshot_version:    Schema version of DriveIntelligenceProfile (e.g. "1.0").
        analysis_version:    Pipeline version that produced this snapshot (e.g. "4.3.0").
        intelligence_payload: Serialized DriveIntelligenceProfile as JSONB.
        created_at:          UTC timestamp of snapshot creation.
        metadata_payload:    Arbitrary pipeline metadata (engine timings, flags, etc.).
    """

    __tablename__ = "drive_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    drive_id = Column(
        Integer,
        ForeignKey("drives.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Phase 4.3 — Provenance: the exact DriveSource analyzed
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drive_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Phase 4.3 — Provenance: the analysis run that produced this snapshot
    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drive_analyses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Schema version of DriveIntelligenceProfile (e.g. "v1.0")
    snapshot_version = Column(String, nullable=False)

    # Version of the analysis pipeline that produced it (e.g. "4.3.0")
    analysis_version = Column(String, nullable=False)

    # Phase 4.3 — LLM prompt version used (e.g. "v1")
    prompt_version = Column(String(20), nullable=True)

    # Phase 4.3 — LLM model used (e.g. "gemini-1.5-pro")
    model_name = Column(String(100), nullable=True)

    # Phase 4.3 — Intelligence schema version (e.g. "v1.0")
    # Denormalized from DriveIntelligenceProfile.intelligence_schema_version
    # for fast querying without deserializing the JSONB payload.
    intelligence_schema_version = Column(String(20), nullable=True)

    # The full serialized DriveIntelligenceProfile inside a metadata wrapper
    intelligence_payload = Column(JSONB, nullable=False)

    # Optional: additional pipeline metadata (timings, flags, engine info)
    metadata_payload = Column(JSONB, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Bidirectional relationship back to Drive
    drive: Mapped["Drive"] = relationship("Drive", back_populates="drive_snapshots")

    # Phase 4.3 — back-reference to the analysis that created this snapshot
    analysis: Mapped[Optional["DriveAnalysis"]] = relationship(
        "DriveAnalysis",
        foreign_keys="DriveSnapshotModel.analysis_id",
        back_populates="snapshot",
        uselist=False,
    )

    __table_args__ = (
        # Composite index to optimize get_latest_snapshot() query
        # (mirrors ix_candidate_intelligence_snapshots_resume_latest)
        Index(
            "ix_drive_snapshots_drive_latest",
            "drive_id",
            "created_at",
            postgresql_using="btree",
            postgresql_ops={"created_at": "DESC NULLS LAST"},
        ),
        # GIN index on JSONB for high-performance Phase 5 retrieval
        Index(
            "ix_drive_snapshots_intelligence",
            "intelligence_payload",
            postgresql_using="gin",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DriveSnapshot id={self.id} "
            f"drive_id={self.drive_id} created_at={self.created_at}>"
        )
