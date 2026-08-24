"""
app/schemas/resume.py
---------------------
Pydantic v2 schemas for SkillFit Phase 3.2 Resume Upload System.

Scope:
    - ResumeResponse: Outbound schema for a single resume record.
    - ResumeListResponse: Outbound schema for a list of resume records.

Design rules (mirrors app/schemas/auth.py conventions):
    - No business logic.
    - No database code.
    - No file-system code.
    - Sensitive / internal fields (file_path, file_hash, extracted_text)
      are deliberately excluded from all response schemas.
    - `from_attributes=True` enables ORM-to-schema conversion via Pydantic v2.
"""

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ResumeResponse(BaseModel):
    """
    Outbound representation of a single uploaded resume.

    Intentionally excludes:
        - file_path  (internal storage path — not a public URL)
        - file_hash  (internal deduplication field)
        - extracted_text  (Phase 3.3 concern)

    file_size is included to allow the frontend to display upload metadata
    and to support future storage-quota dashboards.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the resume record (UUID v4).",
    )
    file_name: str = Field(
        ...,
        description="Original filename as submitted by the student.",
    )
    file_type: str = Field(
        ...,
        description="File extension of the uploaded resume (e.g. '.pdf', '.docx').",
    )
    file_size: int = Field(
        ...,
        description="File size in bytes.",
    )
    is_active: bool = Field(
        ...,
        description="Whether this resume is the active/current version.",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the resume was uploaded.",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp of the last update to this record.",
    )


class ResumeListResponse(BaseModel):
    """
    Outbound representation of all resumes owned by the authenticated student.

    Returns resumes in insertion order (most recent first is handled at the
    service layer via ORDER BY created_at DESC).
    """

    model_config = ConfigDict(from_attributes=True)

    resumes: List[ResumeResponse] = Field(
        ...,
        description="List of resume records belonging to the authenticated student.",
    )
    total: int = Field(
        ...,
        description="Total number of resumes returned.",
    )
