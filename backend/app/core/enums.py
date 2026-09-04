"""
app/core/enums.py
-----------------
Shared application-level enums.

All modules (models, schemas, services, dependencies, routes) must import
enums from here — never redefine them elsewhere. This prevents circular
imports because this file has zero internal application imports; it only
uses the Python standard library.

Phase history:
    Phase 2-3 — UserRole, AnalysisStatus, ResumeType, ProcessingStatus, etc.
    Phase 4.1 — DriveStatus, DriveSourceType
    Phase 4.2 — DriveSourceFormat, DriveSourceProcessingStatus, DriveSourceValidationStatus
"""

import enum


class UserRole(str, enum.Enum):
    """Roles available in the SkillFit platform."""
    student = "student"
    faculty = "faculty"
    admin = "admin"

class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class ConfidenceLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class ReadinessLevel(str, enum.Enum):
    placement_ready = "placement_ready"
    moderately_ready = "moderately_ready"
    needs_improvement = "needs_improvement"

class ComplexityLabel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"

class TechnicalDepthLabel(str, enum.Enum):
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"

class ExperienceStrengthLabel(str, enum.Enum):
    weak = "weak"
    moderate = "moderate"
    strong = "strong"

class RecordSource(str, enum.Enum):
    resume = "resume"
    manual = "manual"
    imported = "imported"

class ResumeType(str, enum.Enum):
    """
    Supported resume categories on the SkillFit platform.

    Each student may hold exactly one resume per type simultaneously:
        generic      — A general-purpose resume covering all skills and experience.
        specialized  — A role-specific or domain-targeted resume.

    Business rule: max 2 active resumes per student (1 generic + 1 specialized).
    Uploading a new resume of an existing type automatically replaces the old one.
    """
    generic     = "generic"
    specialized = "specialized"

class ProcessingStatus(str, enum.Enum):
    """
    Lifecycle status of the automated resume processing pipeline.

    Transitions:
        uploaded   → File stored, pipeline not yet started.
        processing → Background pipeline is actively running.
        completed  → All pipeline stages finished successfully.
        failed     → One or more pipeline stages encountered an error.
    """
    uploaded   = "uploaded"
    processing = "processing"
    completed  = "completed"
    failed     = "failed"


class DriveStatus(str, enum.Enum):
    """
    Lifecycle status of a Placement Drive entity.

    Phase 4.1 — foundation lifecycle only. Intelligence generation
    transitions (analyzing, intelligence_ready) will be added in Phase 4.3.

    Transitions:
        draft  → Drive created; not yet published to candidates.
        active → Drive is live and accepting candidate interest.
        closed → Drive has concluded; no further activity expected.
    """
    draft  = "draft"
    active = "active"
    closed = "closed"


class DriveSourceType(str, enum.Enum):
    """
    Describes how the Placement Drive record was created.

    Phase 4.1 — manual only. Parsed (from JD PDF/text) will be added in
    Phase 4.2 when the Drive Ingestion pipeline is implemented.

    Values:
        manual → Drive data was entered by an admin through the API.
        parsed → Drive data was extracted from a raw job description (Phase 4.2+).
    """
    manual = "manual"
    parsed = "parsed"


class DriveSourceFormat(str, enum.Enum):
    """
    Format of the raw job description source.

    Phase 4.2 — Ingestion pipeline format tracking.

    Values:
        pdf  → Source was uploaded as a PDF file.
        text → Source was submitted as raw text (manual entry).
    """
    pdf  = "pdf"
    text = "text"


class DriveSourceProcessingStatus(str, enum.Enum):
    """
    Lifecycle status of a DriveSource through the ingestion pipeline.

    Phase 4.2 — Ingestion pipeline tracking.

    Transitions:
        uploaded   → File/text received and stored; ingestion not yet started.
        processing → Extraction and normalization are actively running.
        completed  → All pipeline stages finished successfully.
        failed     → One or more pipeline stages encountered an error.
    """
    uploaded   = "uploaded"
    processing = "processing"
    completed  = "completed"
    failed     = "failed"


class DriveSourceValidationStatus(str, enum.Enum):
    """
    Validation status of the ingested source content.

    Phase 4.2 — Source content validation tracking.

    Values:
        pending → Validation has not yet been performed.
        valid   → Source passed all validation checks.
        invalid → Source failed one or more validation checks.
    """
    pending = "pending"
    valid   = "valid"
    invalid = "invalid"
