from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Date, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Drive(Base):
    """Placement drive posted by a company. Independent entity — not owned by a student."""

    __tablename__ = "drives"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(150), nullable=False)
    job_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    package: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    eligibility_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    application_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    # Fix #9: Add updated_at for consistency with all other models
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="drive", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Drive id={self.id} company={self.company_name!r} role={self.role!r}>"