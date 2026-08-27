from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, String, Enum as SQLAlchemyEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.db.database import Base
from app.core.enums import RecordSource


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Fix #7: Removed Optional — issuer is nullable=False at DB level
    issuer: Mapped[str] = mapped_column(String(150), nullable=False)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    technical_depth_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    industry_relevance: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    source: Mapped[RecordSource] = mapped_column(SQLAlchemyEnum(RecordSource), nullable=False, default=RecordSource.manual)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="certifications")
    resume_file: Mapped["ResumeFile"] = relationship("ResumeFile", back_populates="certifications")

    def __repr__(self) -> str:
        return f"<Certification id={self.id} name={self.name!r}>"