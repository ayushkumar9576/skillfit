"""
app/analysis/models/base.py
---------------------------
Core foundational primitives and metadata structures for the SkillFit
Analysis Domain Model Layer (Phase 3.5).

Provides:
    - AnalysisEvidence: Traceable evidence supporting an analytical finding.
    - AnalysisMetadata: Immutable generation context and engine versioning.

Design Rules:
    - Pure standard library dataclasses only.
    - Zero framework dependencies (no SQLAlchemy, FastAPI, Pydantic, or OpenAI).
    - Immutable where practical, fully serializable via dataclasses.asdict().
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class AnalysisEvidence:
    """
    Represents verifiable evidence extracted from resume text that supports
    a specific analytical finding or extraction claim.

    Attributes:
        evidence_text: The verbatim or normalized statement from the resume.
        source_section: Canonical section where the evidence originated (e.g. 'projects', 'skills').
        confidence: Confidence score of this extraction (0.0 to 1.0).
        context_snippet: Surrounding sentence or paragraph for human auditability.
        line_number: Line index in the normalized resume text for pinpoint traceability.
    """
    evidence_text: str
    source_section: str
    confidence: float = 1.0
    context_snippet: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class AnalysisMetadata:
    """
    Immutable domain metadata describing the origin and generation parameters
    of an analysis artifact.

    Attributes:
        source_resume_id: Unique identifier for the source resume document.
        analysis_version: Semantic schema version of the analysis output.
        generated_at: Native UTC timestamp when analysis was generated.
        model_name: Optional identifier of the engine/model utilized (e.g. 'rule_based', 'gpt-4o-mini').
        execution_time_ms: Total computation duration in milliseconds.
    """
    source_resume_id: str
    analysis_version: str = "3.5.0"
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model_name: Optional[str] = None
    execution_time_ms: Optional[float] = None
