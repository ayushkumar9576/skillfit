import uuid
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Enum as SAEnum, ForeignKey, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.db.database import Base


class ImportType(enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"


class ImportStatus(enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ImportAuditLog(Base):
    """
    Audit log for bulk imports.
    """
    __tablename__ = "import_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    import_type: Mapped[ImportType] = mapped_column(
        SAEnum(ImportType, name="import_type"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    imported_rows: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    failed_rows: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    
    status: Mapped[ImportStatus] = mapped_column(
        SAEnum(ImportStatus, name="import_status"), nullable=False, server_default="SUCCESS"
    )
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ImportAuditLog(id={self.id}, type='{self.import_type.value}', file='{self.file_name}', imported={self.imported_rows})>"
