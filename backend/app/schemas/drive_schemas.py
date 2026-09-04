"""
app/schemas/drive_schemas.py
------------------------------
Pydantic v2 schemas for the Phase 4.1 Drive Intelligence Foundation API.

Phase history:
    Phase 4.1 — Initial schemas for Drive CRUD and snapshot retrieval.

Design rules (mirrors app/schemas/resume.py conventions):
    - No business logic, no database code, no file-system code.
    - `from_attributes=True` enables ORM-to-schema conversion via Pydantic v2.
    - All response schemas explicitly exclude internal/sensitive fields.
    - Request schemas perform only structural validation — business rules
      live in the service layer.

Scope (Phase 4.1 only):
    - DriveCreateRequest   — payload for POST /api/v1/drives
    - DriveUpdateRequest   — payload for PATCH /api/v1/drives/{id}
    - DriveResponse        — outbound schema for a single Drive
    - DriveListResponse    — outbound schema for a list of Drives
    - DriveSnapshotResponse — outbound schema for snapshot retrieval (Phase 4.3+)
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import DriveStatus, DriveSourceType


# ---------------------------------------------------------------------------
# Request Schemas (Inbound)
# ---------------------------------------------------------------------------


class DriveCreateRequest(BaseModel):
    """
    Payload for POST /api/v1/drives.

    Validates the incoming drive creation request. All optional fields
    allow partial data entry; the service layer handles defaults.
    """

    company_name: str = Field(
        ...,
        max_length=200,
        description="Name of the hiring company.",
    )
    role: str = Field(
        ...,
        max_length=150,
        description="Role/position title for this placement drive.",
    )
    job_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Employment type (e.g. 'Full-time', 'Internship').",
    )
    location: Optional[str] = Field(
        None,
        max_length=150,
        description="Work location (e.g. 'Remote', 'Bangalore', 'Hybrid').",
    )
    package: Optional[str] = Field(
        None,
        max_length=100,
        description="Compensation package (e.g. '12 LPA', '₹8,00,000 per annum').",
    )
    eligibility_criteria: Optional[str] = Field(
        None,
        description="Free-text eligibility criteria. Structured parsing is Phase 4.2.",
    )
    description: Optional[str] = Field(
        None,
        description="Full job description text. Intelligence extraction is Phase 4.3.",
    )
    application_deadline: Optional[date] = Field(
        None,
        description="Application closing date.",
    )
    required_skills: Optional[List[str]] = Field(
        default_factory=list,
        description="Manually specified required skills (raw list, not normalized yet).",
    )
    preferred_skills: Optional[List[str]] = Field(
        default_factory=list,
        description="Manually specified preferred/nice-to-have skills.",
    )
    structured_eligibility: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Structured eligibility criteria (CGPA, branch, etc.).",
    )
    status: DriveStatus = Field(
        DriveStatus.draft,
        description="Initial lifecycle status. Defaults to 'draft'.",
    )
    source_type: DriveSourceType = Field(
        DriveSourceType.manual,
        description="Data source. Phase 4.1 supports 'manual' only.",
    )


class DriveUpdateRequest(BaseModel):
    """
    Payload for PATCH /api/v1/drives/{id}.

    All fields are optional — only provided fields are updated (partial update).
    """

    company_name: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, max_length=150)
    job_type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=150)
    package: Optional[str] = Field(None, max_length=100)
    eligibility_criteria: Optional[str] = None
    description: Optional[str] = None
    application_deadline: Optional[date] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    structured_eligibility: Optional[Dict[str, Any]] = None
    status: Optional[DriveStatus] = Field(
        None,
        description="Update drive lifecycle status.",
    )


# ---------------------------------------------------------------------------
# Response Schemas (Outbound)
# ---------------------------------------------------------------------------


class DriveResponse(BaseModel):
    """
    Outbound representation of a single Placement Drive.

    Used by: POST /api/v1/drives, GET /api/v1/drives/{id}.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique integer identifier of the drive.")
    company_name: str
    role: str
    job_type: Optional[str] = None
    location: Optional[str] = None
    package: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    description: Optional[str] = None
    application_deadline: Optional[date] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    structured_eligibility: Optional[Dict[str, Any]] = None
    status: DriveStatus
    source_type: DriveSourceType
    created_at: datetime
    updated_at: datetime


class DriveListResponse(BaseModel):
    """
    Outbound representation of a list of Placement Drives.

    Used by: GET /api/v1/drives.
    """

    model_config = ConfigDict(from_attributes=True)

    drives: List[DriveResponse] = Field(..., description="List of placement drives.")
    total: int = Field(..., description="Total number of drives returned.")


class DriveSnapshotResponse(BaseModel):
    """
    Outbound representation of a Drive Intelligence Snapshot.

    Phase 4.1: Table exists; this schema is defined for future use by
    Phase 4.3 when intelligence generation begins populating snapshots.

    Used by: GET /api/v1/drives/{id}/snapshot (Phase 4.3+).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID of the snapshot record.")
    drive_id: int = Field(..., description="Source drive integer PK.")
    snapshot_version: str = Field(..., description="Schema version of DriveIntelligenceProfile.")
    analysis_version: str = Field(..., description="Pipeline version that produced this snapshot.")
    intelligence_payload: Dict[str, Any] = Field(
        ...,
        description="Full serialized DriveIntelligenceProfile.",
    )
    metadata_payload: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional pipeline metadata (timings, flags, etc.).",
    )
    created_at: datetime = Field(..., description="UTC timestamp of snapshot creation.")
