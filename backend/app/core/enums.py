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
