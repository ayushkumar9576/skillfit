import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional
from app.db.database import Base


class ResumeFile(Base):
    __tablename__ = "resume_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Fix #3: Use server_default so DB-level inserts (raw SQL, triggers) also get True
    is_active: Mapped[bool] = mapped_column(server_default="true", nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="resume_files")
    cv_analysis: Mapped["CVAnalysis"] = relationship(
        "CVAnalysis", back_populates="resume_file", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("student_id", "file_hash", name="uq_student_resume_hash"),
    )

    def __repr__(self) -> str:
        return f"<ResumeFile id={self.id} student_id={self.student_id}>"
