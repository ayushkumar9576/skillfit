from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=False)
    cgpa: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    resume_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    placement_status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Not Placed"
    )
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    faculty_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    faculty: Mapped[Optional["Faculty"]] = relationship("Faculty", back_populates="students")
    projects: Mapped[List["StudentProject"]] = relationship(
        "StudentProject", back_populates="student", cascade="all, delete-orphan"
    )
    skills: Mapped[List["StudentSkill"]] = relationship(
        "StudentSkill", back_populates="student", cascade="all, delete-orphan"
    )
    certifications: Mapped[List["Certification"]] = relationship(
        "Certification", back_populates="student", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Student id={self.id} name={self.name!r}>"