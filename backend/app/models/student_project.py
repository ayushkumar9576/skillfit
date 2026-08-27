from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, Enum as SQLAlchemyEnum, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.db.database import Base
from app.core.enums import ComplexityLabel, TechnicalDepthLabel, RecordSource


class StudentProject(Base):
    """Projects extracted from a student's CV (source for future AI analysis)."""

    __tablename__ = "student_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False, index=True
    )

    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Fix #7: Removed Optional — description is a required field (nullable=False at DB level)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Fix #8: tech_stack retained as required field until JSONB migration is planned
    tech_stack: Mapped[str] = mapped_column(String(500), nullable=False)

    complexity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    complexity_label: Mapped[Optional[ComplexityLabel]] = mapped_column(SQLAlchemyEnum(ComplexityLabel), nullable=True)

    technical_depth_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    technical_depth_label: Mapped[Optional[TechnicalDepthLabel]] = mapped_column(SQLAlchemyEnum(TechnicalDepthLabel), nullable=True)

    skills_demonstrated: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    source: Mapped[RecordSource] = mapped_column(SQLAlchemyEnum(RecordSource), nullable=False, default=RecordSource.manual)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="projects")
    resume_file: Mapped["ResumeFile"] = relationship("ResumeFile", back_populates="projects")

    def __repr__(self) -> str:
        return f"<StudentProject id={self.id} name={self.project_name!r}>"