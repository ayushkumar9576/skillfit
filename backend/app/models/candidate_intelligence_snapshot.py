"""
app/models/candidate_intelligence_snapshot.py
---------------------------------------------
Stores versioned JSONB snapshots of the CandidateIntelligenceProfile.

Phase 3.13A: Initial model.
Phase 3.14: Added ForeignKey constraint on resume_id and bidirectional
            relationship to ResumeFile for proper cascade-delete behaviour.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.resume_file import ResumeFile


class CandidateIntelligenceSnapshotModel(Base):
    __tablename__ = "candidate_intelligence_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Phase 3.14: FK added so db.delete(resume) cascades snapshot cleanup
    resume_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resume_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Schema version of CandidateIntelligenceProfile (e.g., "1.0")
    profile_version = Column(String, nullable=False)

    # Version of the analysis pipeline that produced it (e.g., "4.0.0")
    analysis_version = Column(String, nullable=False)

    # The serialized profile inside a metadata wrapper
    profile_json = Column(JSONB, nullable=False)

    generated_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Bidirectional relationship — Phase 3.14
    resume_file = relationship(
        "ResumeFile",
        back_populates="candidate_intelligence_snapshots",
    )

    __table_args__ = (
        # Composite index to optimize get_latest_snapshot() query
        Index(
            "ix_candidate_intelligence_snapshots_resume_latest",
            "resume_id",
            "generated_at",
            postgresql_using="btree",
            postgresql_ops={"generated_at": "DESC NULLS LAST"},
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CandidateIntelligenceSnapshot id={self.id} "
            f"resume_id={self.resume_id} generated_at={self.generated_at}>"
        )
