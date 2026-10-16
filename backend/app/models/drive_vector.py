import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.schema import Index

from app.db.database import Base

class DriveVectorModel(Base):
    """
    ORM model for Drive Vectors (Phase 5.2).
    Stores canonical ML vector representation derived from DriveIntelligenceProfile.
    """

    __tablename__ = "drive_vectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK to drive
    drive_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drives.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Provenance: which exact snapshot generated this vector?
    source_snapshot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("drive_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )

    schema_version = Column(Integer, nullable=False)

    vector_json = Column(JSONB, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("drive_id", "schema_version", name="uq_drive_vector_schema"),
        # Index on drive_id and schema_version for fast UPSERTs
        Index("ix_drive_vectors_drive_schema", "drive_id", "schema_version"),
    )

    def __repr__(self) -> str:
        return f"<DriveVector id={self.id} drive_id={self.drive_id} schema_version={self.schema_version}>"
