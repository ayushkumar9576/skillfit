from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[Optional[str]] = mapped_column(String(150), nullable=False)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="certifications")

    def __repr__(self) -> str:
        return f"<Certification id={self.id} name={self.name!r}>"