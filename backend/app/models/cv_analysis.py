import uuid
from datetime import datetime
from typing import Optional

# Fix #6: Removed unused `Integer` import
from sqlalchemy import ForeignKey, String, Text, Enum as SQLAlchemyEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.core.enums import AnalysisStatus, ReadinessLevel


class CVAnalysis(Base):
    __tablename__ = "cv_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Fix #4: Added server_default so DB-level inserts also receive the correct default
    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        SQLAlchemyEnum(AnalysisStatus), nullable=False, default=AnalysisStatus.pending, server_default="pending"
    )
    # Fix #5: summary and readiness_explanation are nullable → must be Optional
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    weaknesses: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Fix #5: readiness_level is nullable → must be Optional
    readiness_level: Mapped[Optional[ReadinessLevel]] = mapped_column(SQLAlchemyEnum(ReadinessLevel), nullable=True)
    readiness_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    analysis_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="cv_analyses")
    resume_file: Mapped["ResumeFile"] = relationship("ResumeFile", back_populates="cv_analysis")

    def __repr__(self) -> str:
        return f"<CVAnalysis id={self.id} status={self.analysis_status}>"
