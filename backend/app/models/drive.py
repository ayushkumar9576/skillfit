"""
app/models/drive.py
-------------------
Placement Drive entity — the root source entity for all Drive Intelligence.

Phase history:
    Pre-4.0   — Initial model: company_name, role, required_skills, etc.
    Phase 4.1 — Added `status` (DriveStatus) and `source_type` (DriveSourceType)
                for entity lifecycle tracking.
                Added `drive_snapshots` relationship for the Drive Intelligence
                persistence layer.

Design:
    Drive is the source entity equivalent of ResumeFile on the Candidate side.
    All Drive Intelligence flows from this root entity:

        Drive
          ↓
        DriveSnapshotModel   (Phase 4.1 — storage foundation)
          ↓
        DriveAnalysis        (Phase 4.3 — intelligence pipeline tracking)
"""

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Date, Enum as SQLAlchemyEnum, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.core.enums import DriveStatus, DriveSourceType


class Drive(Base):
    """
    Placement drive posted by a company.

    Independent entity — not owned by a student or faculty member.
    Serves as the root entity for Drive Intelligence generation (Phase 4+).
    """

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

    required_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    preferred_skills: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    structured_eligibility: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Phase 4.1 — entity lifecycle tracking
    status: Mapped[DriveStatus] = mapped_column(
        SQLAlchemyEnum(DriveStatus, name="drivestatus"),
        nullable=False,
        default=DriveStatus.draft,
        server_default="draft",
    )
    source_type: Mapped[DriveSourceType] = mapped_column(
        SQLAlchemyEnum(DriveSourceType, name="drivesourcetype"),
        nullable=False,
        default=DriveSourceType.manual,
        server_default="manual",
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Existing relationships
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="drive", cascade="all, delete-orphan"
    )

    # Phase 4.1 — Drive Intelligence persistence relationship
    drive_snapshots: Mapped[List["DriveSnapshotModel"]] = relationship(
        "DriveSnapshotModel",
        back_populates="drive",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Drive id={self.id} company={self.company_name!r} "
            f"role={self.role!r} status={self.status.value}>"
        )