from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Recommendation(Base):

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    drive_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("drives.id", ondelete="CASCADE"), nullable=False, index=True
    )

    match_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recommendation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Recommended"
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    # Fix #9: Add updated_at for consistency with all other models
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="recommendations")
    drive: Mapped["Drive"] = relationship("Drive")

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} student_id={self.student_id} drive_id={self.drive_id} score={self.match_score}>"