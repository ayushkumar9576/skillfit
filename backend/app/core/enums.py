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
    """
    Roles available in the SkillFit platform.

    Inherits from str so that SQLAlchemy's Enum column and Pydantic's
    JSON serialization both receive a plain string value (e.g. "student")
    rather than the enum member object.

    Phase 2 implements: student, faculty.
    admin is defined in the enum but not implemented in Phase 2.
    """

    student = "student"
    faculty = "faculty"
    admin = "admin"
