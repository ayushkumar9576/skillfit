import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, func, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    source_resume_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="SET NULL"), nullable=True, index=True
    )

    primary_domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    secondary_domains: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    domain_tiers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    domain_scores: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    domain_signals: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    project_tiers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    industry_exposure_levels: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    candidate_primary_domain_confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    
    strongest_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    soft_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    role_affinities: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    evidence_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    readiness_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    readiness_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    profile_completeness_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    normalized_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    generated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    analysis_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="candidate_profile")
    source_resume: Mapped[Optional["ResumeFile"]] = relationship("ResumeFile", back_populates="candidate_profiles")

    def __repr__(self) -> str:
        return f"<CandidateProfile id={self.id} student_id={self.student_id}>"
