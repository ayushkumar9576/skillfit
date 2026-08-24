import uuid
from datetime import datetime
from typing import Optional

from app.core.enums import UserRole

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base



class User(Base):
    """
    Single source of truth for identity and authentication.
    Stores: full_name, email, registration_number, credentials, role, account status.
    Does NOT store: academic data, faculty details, placement information.

    registration_number is the primary business identifier used across all
    university workflows (placement, analytics, dashboards, reporting).
    It is stored here — on the auth entity — so login and identity resolution
    require no joins to Student or Faculty tables.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    registration_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False, index=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    student: Mapped[Optional["Student"]] = relationship("Student", back_populates="user", uselist=False)
    faculty: Mapped[Optional["Faculty"]] = relationship("Faculty", back_populates="user", uselist=False)

    def __repr__(self) -> str:
        # Deliberately excludes password_hash from repr/logs.
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"