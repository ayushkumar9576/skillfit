import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Student(Base):
    """
    Phase 3.14 baseline — all legacy analysis relationships removed.
    """
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    registration_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cgpa: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active_backlogs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    profile_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    placement_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Not Placed"
    )

    faculty_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Active relationships — Phase 3.14 baseline
    user: Mapped["User"] = relationship("User", back_populates="student")
    faculty: Mapped[Optional["Faculty"]] = relationship("Faculty", back_populates="students")
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="student", cascade="all, delete-orphan"
    )
    resume_files: Mapped[List["ResumeFile"]] = relationship(
        "ResumeFile", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} user_id={self.user_id}>"