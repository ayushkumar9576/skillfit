from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Enum as SQLAlchemyEnum, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.db.database import Base
from app.core.enums import ConfidenceLevel, RecordSource


class StudentSkill(Base):
    """Evidence-based skill assessment — the core of SkillFit's profiling philosophy."""

    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False, index=True
    )

    skill_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    confidence_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_level: Mapped[Optional[ConfidenceLevel]] = mapped_column(SQLAlchemyEnum(ConfidenceLevel), nullable=True)
    evidence_sources: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    source: Mapped[RecordSource] = mapped_column(SQLAlchemyEnum(RecordSource), nullable=False, default=RecordSource.manual)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="skills")
    resume_file: Mapped["ResumeFile"] = relationship("ResumeFile", back_populates="skills")

    def __repr__(self) -> str:
        return f"<StudentSkill id={self.id} skill={self.skill_name!r} confidence={self.confidence_score}>"