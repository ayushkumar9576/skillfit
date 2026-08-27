from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, Enum as SQLAlchemyEnum, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.db.database import Base
from app.core.enums import ExperienceStrengthLabel, RecordSource


class StudentInternship(Base):
    __tablename__ = "student_internships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False, index=True
    )

    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    # Fix #5: Nullable fields correctly annotated as Optional
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    technologies_used: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    experience_strength_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    experience_strength_label: Mapped[Optional[ExperienceStrengthLabel]] = mapped_column(
        SQLAlchemyEnum(ExperienceStrengthLabel), nullable=True
    )

    source: Mapped[RecordSource] = mapped_column(SQLAlchemyEnum(RecordSource), nullable=False, default=RecordSource.manual)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="internships")
    resume_file: Mapped["ResumeFile"] = relationship("ResumeFile", back_populates="internships")

    def __repr__(self) -> str:
        return f"<StudentInternship id={self.id} company={self.company_name}>"
