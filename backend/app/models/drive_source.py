"""
app/models/drive_source.py
---------------------------
Versioned source records for Placement Drive job descriptions.

Phase 4.2 — Drive Ingestion & Parsing foundation model.

Design:
    DriveSource is the ingestion-layer entity that tracks every version of
    raw job description content uploaded for a given Drive.

    It sits between the Drive entity and the Drive Intelligence layer:

        Drive
         ├─ DriveSource V1   (Phase 4.2 — raw PDF/text + normalised content)
         ├─ DriveSource V2
         └─ DriveSource V3

        DriveSource V3
              ↓
        Drive Intelligence Analysis   (Phase 4.3)
              ↓
        DriveSnapshot V1              (Phase 4.3)

    DriveSource answers:  "What does the source contain?"
    DriveSnapshot answers: "What does the source mean?"

Immutability contract:
    DriveSource rows are NEVER updated after processing completes.
    Each new upload creates a new row with an incremented `version`.
    This guarantees full auditability and future reprocessing capability.

Duplicate strategy:
    If identical content (same content_hash) is re-uploaded for the same drive,
    a new version row is still created.  The duplicate is flagged via
    processing_metadata["is_duplicate"] = True so it is never silently discarded.
    Auditability always wins.

Unique constraint:
    (drive_id, version) is UNIQUE at the DB level to prevent accidental
    duplicate version creation from concurrent requests.

Phase roadmap for this file:
    Phase 4.2 — Initial model: ingestion, validation, normalisation.
    Phase 4.3 — DriveSource rows are consumed by the intelligence pipeline;
                 no structural changes expected here.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.schema import Index

from app.db.database import Base
from app.core.enums import (
    DriveSourceFormat,
    DriveSourceProcessingStatus,
    DriveSourceValidationStatus,
)

if TYPE_CHECKING:
    from app.models.drive import Drive


class DriveSource(Base):
    """
    ORM model for a single versioned job description source upload.

    Each row represents one ingested job description — either from a PDF upload
    or raw text submission.  Multiple rows may exist for the same drive as the
    JD evolves over time.

    Attributes:
        id:                   UUID primary key.
        drive_id:             FK to drives.id — cascade deletes remove sources.
        version:              Monotonically increasing integer per drive.
                              Managed explicitly by the service layer.
                              (drive_id, version) is UNIQUE at the DB level.
        source_format:        Input format — pdf or text.
        original_filename:    Client-supplied filename (stored for auditability only).
                              Never used for file I/O — disk path is always UUID-based.
        file_path:            Storage path managed by StorageProvider.
                              None for text-only sources.
        content_hash:         SHA-256 of the raw source bytes.
                              Used for duplicate detection and integrity verification.
        extraction_method:    Human-readable label for the extractor used
                              (e.g. "pdfplumber", "raw_text").
        extractor_version:    Version of the extraction component (e.g. "v1.0").
        parser_version:       Version of the normalization component (e.g. "v1.0").
        processing_status:    Lifecycle status through the ingestion pipeline.
        validation_status:    Content validation result.
        raw_content:          Unmodified extracted text from the source.
        normalized_content:   Whitespace/encoding-normalized text. Phase 4.3 input.
        character_count:      Character count of the normalized content.
        word_count:           Word count of the normalized content.
        processing_metadata:  JSONB bag for pipeline metadata:
                                - is_duplicate (bool)
                                - duplicate_of_version (int, if is_duplicate)
                                - validation_errors (list[str])
                                - extractor_warnings (list[str])
        created_at:           UTC timestamp when this row was first persisted.
        processed_at:         UTC timestamp when pipeline processing completed.
                              Distinct from created_at to support future async
                              processing where upload and processing are decoupled.
    """

    __tablename__ = "drive_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    drive_id = Column(
        Integer,
        ForeignKey("drives.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Explicitly managed version number — not inferred from row order
    version = Column(Integer, nullable=False)

    # -----------------------------------------------------------------------
    # Source provenance
    # -----------------------------------------------------------------------

    source_format = Column(
        SQLAlchemyEnum(DriveSourceFormat, name="drivesourceformat"),
        nullable=False,
    )

    # Original client filename — stored for auditability only, never for I/O
    original_filename = Column(String(500), nullable=True)

    # Storage path via StorageProvider — None for text-only sources
    file_path = Column(String(1000), nullable=True)

    # -----------------------------------------------------------------------
    # Integrity
    # -----------------------------------------------------------------------

    # SHA-256 hex digest of the raw source bytes
    content_hash = Column(String(64), nullable=False, index=True)

    # -----------------------------------------------------------------------
    # Pipeline provenance
    # -----------------------------------------------------------------------

    extraction_method = Column(String(100), nullable=True)
    extractor_version = Column(String(20), nullable=True)
    parser_version = Column(String(20), nullable=True)

    # -----------------------------------------------------------------------
    # Lifecycle status
    # -----------------------------------------------------------------------

    processing_status = Column(
        SQLAlchemyEnum(DriveSourceProcessingStatus, name="drivesourceprocessingstatus"),
        nullable=False,
        default=DriveSourceProcessingStatus.uploaded,
        server_default="uploaded",
    )

    validation_status = Column(
        SQLAlchemyEnum(DriveSourceValidationStatus, name="drivesourcevalidationstatus"),
        nullable=False,
        default=DriveSourceValidationStatus.pending,
        server_default="pending",
    )

    # -----------------------------------------------------------------------
    # Content — Phase 4.2 output is fundamentally text; no JSONB here
    # -----------------------------------------------------------------------

    raw_content = Column(Text, nullable=True)
    normalized_content = Column(Text, nullable=True)

    # Content statistics for validation, debugging, and anomaly detection
    character_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)

    # -----------------------------------------------------------------------
    # Metadata bag
    # -----------------------------------------------------------------------

    # Flexible JSONB bag for pipeline metadata:
    #   is_duplicate, duplicate_of_version, validation_errors, extractor_warnings, etc.
    processing_metadata = Column(JSONB, nullable=True)

    # -----------------------------------------------------------------------
    # Timestamps
    # -----------------------------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Tracked separately from created_at to support future async processing
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # -----------------------------------------------------------------------
    # Relationships
    # -----------------------------------------------------------------------

    drive: Mapped["Drive"] = relationship("Drive", back_populates="drive_sources")

    # -----------------------------------------------------------------------
    # Constraints & Indexes
    # -----------------------------------------------------------------------

    __table_args__ = (
        # Prevent concurrent requests from creating duplicate version numbers
        UniqueConstraint("drive_id", "version", name="uq_drive_source_version"),
        # Optimise latest-source lookup per drive
        Index(
            "ix_drive_sources_drive_latest",
            "drive_id",
            "version",
            postgresql_using="btree",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DriveSource id={self.id} drive_id={self.drive_id} "
            f"version={self.version} format={self.source_format} "
            f"status={self.processing_status}>"
        )
