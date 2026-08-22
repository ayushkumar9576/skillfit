from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class StudentSkill(Base):
    """Evidence-based skill assessment — the core of SkillFit's profiling philosophy."""

    __tablename__ = "student_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    skill_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    confidence_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="skills")

    def __repr__(self) -> str:
        return f"<StudentSkill id={self.id} skill={self.skill_name!r} confidence={self.confidence_score}>"