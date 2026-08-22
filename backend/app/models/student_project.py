from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class StudentProject(Base):
    """Projects extracted from a student's CV (source for future AI analysis)."""

    __tablename__ = "student_projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=False)
    tech_stack: Mapped[Optional[str]] = mapped_column(String(500), nullable=False)
    complexity_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="projects")

    def __repr__(self) -> str:
        return f"<StudentProject id={self.id} title={self.title!r}>"