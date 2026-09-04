"""
app/schemas/drive_source_schemas.py
-------------------------------------
Pydantic v2 schemas for the Phase 4.2 Drive Ingestion & Parsing API.

Phase history:
    Phase 4.2 — Initial schemas for drive source upload and content retrieval.

Design rules (mirrors app/schemas/drive_schemas.py conventions):
    - No business logic, no database code, no file-system code.
    - `from_attributes=True` enables ORM-to-schema conversion via Pydantic v2.
    - All response schemas explicitly exclude internal/sensitive fields.
    - Request schemas perform only structural validation — business rules
      live in the service layer.

Scope (Phase 4.2):
    - TextSubmissionRequest    — payload for POST /api/v1/drives/{id}/text
    - DriveSourceResponse      — outbound schema for a single DriveSource record
    - DriveSourceListResponse  — outbound schema for list of sources per drive
    - ParsedContentResponse    — outbound schema for the latest parsed content
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    DriveSourceFormat,
    DriveSourceProcessingStatus,
    DriveSourceValidationStatus,
)


# ---------------------------------------------------------------------------
# Request Schemas (Inbound)
# ---------------------------------------------------------------------------


class TextSubmissionRequest(BaseModel):
    """
    Payload for POST /api/v1/drives/{id}/text.

    Submits a raw text job description for ingestion.
    The text is passed through the standard validation → extraction →
    normalisation pipeline, same as a PDF upload.
    """

    text: str = Field(
        ...,
        min_length=50,
        description=(
            "Raw job description text. Minimum 50 characters required. "
            "The text will be normalised but not interpreted."
        ),
    )


# ---------------------------------------------------------------------------
# Response Schemas (Outbound)
# ---------------------------------------------------------------------------


class DriveSourceResponse(BaseModel):
    """
    Outbound representation of a single DriveSource record.

    Used by:
        GET /api/v1/drives/{id}/sources
        GET /api/v1/drives/{id}/sources/{source_id}
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID of the DriveSource record.")
    drive_id: int = Field(..., description="Parent Drive integer PK.")
    version: int = Field(..., description="Monotonic version number within this drive.")
    source_format: DriveSourceFormat = Field(..., description="Input format: pdf or text.")
    original_filename: Optional[str] = Field(
        None, description="Client-supplied filename (for auditability only)."
    )
    content_hash: str = Field(..., description="SHA-256 hex digest of the raw source bytes.")
    extraction_method: Optional[str] = Field(None, description="Extractor used (e.g. pdfplumber).")
    extractor_version: Optional[str] = Field(None, description="Extractor component version.")
    parser_version: Optional[str] = Field(None, description="Normalizer component version.")
    processing_status: DriveSourceProcessingStatus
    validation_status: DriveSourceValidationStatus
    character_count: Optional[int] = Field(None, description="Character count of normalized content.")
    word_count: Optional[int] = Field(None, description="Word count of normalized content.")
    processing_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Pipeline metadata: is_duplicate, duplicate_of_version, "
            "extractor_warnings, normalizer_transformations, etc."
        ),
    )
    created_at: datetime
    processed_at: Optional[datetime] = None

    @classmethod
    def from_orm_with_id(cls, obj: Any) -> "DriveSourceResponse":
        """ORM → schema with UUID id coerced to str."""
        data = {
            "id": str(obj.id),
            "drive_id": obj.drive_id,
            "version": obj.version,
            "source_format": obj.source_format,
            "original_filename": obj.original_filename,
            "content_hash": obj.content_hash,
            "extraction_method": obj.extraction_method,
            "extractor_version": obj.extractor_version,
            "parser_version": obj.parser_version,
            "processing_status": obj.processing_status,
            "validation_status": obj.validation_status,
            "character_count": obj.character_count,
            "word_count": obj.word_count,
            "processing_metadata": obj.processing_metadata,
            "created_at": obj.created_at,
            "processed_at": obj.processed_at,
        }
        return cls(**data)


class DriveSourceListResponse(BaseModel):
    """
    Outbound representation of all DriveSource records for a drive.

    Used by: GET /api/v1/drives/{id}/sources
    """

    model_config = ConfigDict(from_attributes=True)

    drive_id: int
    sources: List[DriveSourceResponse]
    total: int = Field(..., description="Total number of source versions.")


class ParsedContentResponse(BaseModel):
    """
    Outbound representation of the latest parsed content for a drive.

    Exposes the normalized_content (Phase 4.3 input) along with source
    provenance and statistics.  Raw content is intentionally excluded from
    this response — use the sources endpoint for full audit access.

    Used by: GET /api/v1/drives/{id}/content/latest
    """

    model_config = ConfigDict(from_attributes=True)

    drive_id: int
    source_id: str = Field(..., description="UUID of the DriveSource that produced this content.")
    source_version: int
    source_format: DriveSourceFormat
    original_filename: Optional[str] = None
    content_hash: str
    extractor_version: Optional[str] = None
    parser_version: Optional[str] = None
    normalized_content: str = Field(
        ...,
        description="Normalised job description text. This is the Phase 4.3 input contract.",
    )
    character_count: Optional[int] = None
    word_count: Optional[int] = None
    is_duplicate: bool = Field(
        False,
        description="True if this source's content is identical to a previous version.",
    )
    duplicate_of_version: Optional[int] = Field(
        None,
        description="Version number of the earlier duplicate, if is_duplicate=True.",
    )
    created_at: datetime
    processed_at: Optional[datetime] = None


class IngestionResponse(BaseModel):
    """
    Response returned after a successful upload or text submission.

    Provides immediate feedback on the ingestion result without requiring
    the caller to make a follow-up GET request.
    """

    model_config = ConfigDict(from_attributes=True)

    message: str = Field(..., description="Human-readable success message.")
    drive_id: int
    source_id: str
    source_version: int
    source_format: DriveSourceFormat
    character_count: int
    word_count: int
    is_duplicate: bool
    duplicate_of_version: Optional[int] = None
    parser_version: Optional[str] = None
    extractor_version: Optional[str] = None
