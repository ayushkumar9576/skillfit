import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import Optional
from app.db.database import Base
from app.core.enums import ResumeType, ProcessingStatus


class ResumeFile(Base):
    """
    ORM model for uploaded student resume files.

    Phase 3.2  — file storage, validation metadata, deduplication.
    Phase 3.2.1 — security hardening (file_hash unique constraint).
    Pre-3.6   — resume_type (generic/specialized) + processing_status lifecycle.

    Business rules:
        - Each student may have at most 1 active resume per resume_type.
        - (student_id, resume_type) is enforced UNIQUE at the DB level.
        - processing_status tracks the automated pipeline lifecycle.
        - Uploading a new resume of an existing type replaces the old one
          (handled in the service layer before inserting the new record).
    """
    __tablename__ = "resume_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_sections: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Resume category: generic or specialized. Enforced unique per student at DB level.
    resume_type: Mapped[ResumeType] = mapped_column(
        SQLAlchemyEnum(ResumeType, name="resumetype"),
        nullable=False,
        default=ResumeType.generic,
        server_default="generic",
    )

    # Automated pipeline lifecycle status.
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        SQLAlchemyEnum(ProcessingStatus, name="processingstatus"),
        nullable=False,
        default=ProcessingStatus.uploaded,
        server_default="uploaded",
    )

    # Fix #3: Use server_default so DB-level inserts (raw SQL, triggers) also get True
    is_active: Mapped[bool] = mapped_column(server_default="true", nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="resume_files")
    cv_analysis: Mapped["CVAnalysis"] = relationship(
        "CVAnalysis", back_populates="resume_file", uselist=False, cascade="all, delete-orphan"
    )
    projects: Mapped[list["StudentProject"]] = relationship(
        "StudentProject", back_populates="resume_file", cascade="all, delete-orphan"
    )
    internships: Mapped[list["StudentInternship"]] = relationship(
        "StudentInternship", back_populates="resume_file", cascade="all, delete-orphan"
    )
    certifications: Mapped[list["Certification"]] = relationship(
        "Certification", back_populates="resume_file", cascade="all, delete-orphan"
    )
    skills: Mapped[list["StudentSkill"]] = relationship(
        "StudentSkill", back_populates="resume_file", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Deduplication: same student cannot upload identical file content twice.
        UniqueConstraint("student_id", "file_hash", name="uq_student_resume_hash"),
        # Type uniqueness: each student may have at most 1 record per resume_type.
        # This is the database-level enforcement of the 1-generic + 1-specialized rule.
        UniqueConstraint("student_id", "resume_type", name="uq_student_resume_type"),
    )

    def __repr__(self) -> str:
        return f"<ResumeFile id={self.id} student_id={self.student_id} type={self.resume_type}>"
