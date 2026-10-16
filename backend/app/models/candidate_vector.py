import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.schema import Index

from app.db.database import Base

class CandidateVectorModel(Base):
    """
    ORM model for Candidate Vectors (Phase 5.2).
    Stores canonical ML vector representation derived from CandidateIntelligenceProfile.
    """

    __tablename__ = "candidate_vectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK to resume (the primary subject of candidate intelligence)
    resume_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resume_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Provenance: which exact snapshot generated this vector?
    source_snapshot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("candidate_intelligence_snapshots.id", ondelete="SET NULL"),
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
        UniqueConstraint("resume_id", "schema_version", name="uq_candidate_vector_schema"),
        # Index on resume_id and schema_version for fast UPSERTs
        Index("ix_candidate_vectors_resume_schema", "resume_id", "schema_version"),
    )

    def __repr__(self) -> str:
        return f"<CandidateVector id={self.id} resume_id={self.resume_id} schema_version={self.schema_version}>"
