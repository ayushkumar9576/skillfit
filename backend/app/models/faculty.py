from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # One faculty mentors many students
    students: Mapped[List["Student"]] = relationship(
        "Student",
        back_populates="faculty",
    )

    def __repr__(self) -> str:
        return f"<Faculty id={self.id} name={self.name!r}>"