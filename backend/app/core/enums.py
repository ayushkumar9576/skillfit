"""
app/core/enums.py
-----------------
Shared application-level enums.

All modules (models, schemas, services, dependencies, routes) must import
enums from here — never redefine them elsewhere. This prevents circular
imports because this file has zero internal application imports; it only
uses the Python standard library.
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
