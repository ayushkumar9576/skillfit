"""
app/schemas/drive_analysis_schemas.py
---------------------------------------
Pydantic v2 request/response schemas for Phase 4.3 Drive Analysis API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class AnalyzeDriveRequest(BaseModel):
    """
    Optional request body for POST /drives/{id}/analyze.
    All fields have defaults so the endpoint can be called with no body.
    """
    prompt_version: str = Field(
        default="v1",
        description="Prompt template version to use (default: 'v1').",
    )


# ---------------------------------------------------------------------------
# Analysis response schemas
# ---------------------------------------------------------------------------


class AnalysisResponse(BaseModel):
    """Response schema for a single DriveAnalysis record."""

    id: str
    drive_id: int
    source_id: Optional[str]
    snapshot_id: Optional[str]

    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    created_at: datetime

    analysis_version: str
    prompt_version: str
    model_name: str

    error_message: Optional[str]
    processing_metadata: Optional[Dict[str, Any]]

    model_config = {"from_attributes": True}


class AnalysisListResponse(BaseModel):
    """Response schema for GET /drives/{id}/analysis."""
    drive_id: int
    total: int
    analyses: List[AnalysisResponse]


# ---------------------------------------------------------------------------
# Snapshot response schemas
# ---------------------------------------------------------------------------


class SnapshotSummaryResponse(BaseModel):
    """Lightweight snapshot summary for list endpoints."""

    id: str
    drive_id: int
    source_id: Optional[str]
    analysis_id: Optional[str]

    analysis_version: str
    prompt_version: Optional[str]
    model_name: Optional[str]
    intelligence_schema_version: Optional[str]

    created_at: datetime

    model_config = {"from_attributes": True}


class SnapshotDetailResponse(BaseModel):
    """Full snapshot response including the intelligence_payload."""

    id: str
    drive_id: int
    source_id: Optional[str]
    analysis_id: Optional[str]

    analysis_version: str
    prompt_version: Optional[str]
    model_name: Optional[str]
    intelligence_schema_version: Optional[str]

    intelligence_payload: Dict[str, Any]
    metadata_payload: Optional[Dict[str, Any]]

    created_at: datetime

    model_config = {"from_attributes": True}


class SnapshotListResponse(BaseModel):
    """Response schema for GET /drives/{id}/snapshots."""
    drive_id: int
    total: int
    snapshots: List[SnapshotSummaryResponse]
