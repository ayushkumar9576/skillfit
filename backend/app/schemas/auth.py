"""
app/schemas/auth.py
-------------------
Pydantic v2 schemas for SkillFit Phase 2 authentication.

Scope (Phase 2 only):
    - Student registration
    - Faculty registration
    - Login (email + password)
    - JWT token response
    - Authenticated user identity (/auth/me)

Out of scope (deferred to profile management phase):
    - StudentProfileSchema
    - FacultyProfileSchema
    - Any role-conditional composed schema

Design rules enforced here:
    - No business logic
    - No JWT logic
    - No database code
    - `password` appears ONLY on request schemas — never on any response
    - `password_hash` is an ORM-only field — never on any schema
    - `registration_number` is on UserResponseSchema as an identity field;
      the service layer populates it via user.student / user.faculty relationship
"""

import uuid
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import UserRole


# ---------------------------------------------------------------------------
# Request Schemas (Inbound)
# ---------------------------------------------------------------------------


class RegisterStudentSchema(BaseModel):
    """
    Payload for POST /auth/register/student.

    Validates the incoming registration request before any database writes.
    The service layer is responsible for hashing the password and constructing
    the User + Student ORM objects.
    """

    full_name: str = Field(
        ...,
        max_length=150,
        description="Student's full name. Leading/trailing whitespace is stripped.",
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address. Used as the login identifier.",
    )
    password: str = Field(
        ...,
        min_length=12,
        description="Plain-text password. Minimum 12 characters. Hashed by the service layer before storage.",
    )
    registration_number: str = Field(
        ...,
        pattern=r'^\d{8}$',
        description="University-issued registration number. Must be exactly 8 digits and unique.",
    )
    branch: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Academic branch/stream (e.g. 'Computer Science'). Optional at registration.",
    )
    cgpa: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=10.0,
        description="Cumulative GPA on a 10-point scale. Optional at registration.",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Contact phone number. Optional at registration. No format enforced here — validated at profile update.",
    )

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_full_name(cls, v: str) -> str:
        """Strip whitespace and reject blank names."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("full_name must not be blank or whitespace only.")
        return stripped

    @field_validator("registration_number", mode="before")
    @classmethod
    def strip_registration_number(cls, v: str) -> str:
        """Strip whitespace and reject empty registration numbers."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("registration_number must not be blank.")
        return stripped


class RegisterFacultySchema(BaseModel):
    """
    Payload for POST /auth/register/faculty.

    Mirrors RegisterStudentSchema structure but targets the Faculty ORM model.
    Academic/profile fields specific to faculty (department) are optional.
    """

    full_name: str = Field(
        ...,
        max_length=150,
        description="Faculty member's full name. Leading/trailing whitespace is stripped.",
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address. Used as the login identifier.",
    )
    password: str = Field(
        ...,
        min_length=12,
        description="Plain-text password. Minimum 12 characters. Hashed by the service layer before storage.",
    )
    registration_number: str = Field(
        ...,
        pattern=r'^\d{8}$',
        description="University-issued faculty registration number. Must be exactly 8 digits and unique.",
    )
    department: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Academic department (e.g. 'Computer Science & Engineering'). Optional at registration.",
    )

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_full_name(cls, v: str) -> str:
        """Strip whitespace and reject blank names."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("full_name must not be blank or whitespace only.")
        return stripped

    @field_validator("registration_number", mode="before")
    @classmethod
    def strip_registration_number(cls, v: str) -> str:
        """Strip whitespace and reject empty registration numbers."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("registration_number must not be blank.")
        return stripped


class LoginSchema(BaseModel):
    """
    Payload for POST /auth/login.

    Authenticates using university-issued registration_number + password.
    Email is not used for authentication — it is stored on User for
    notifications and future password-reset flows only.
    """

    registration_number: str = Field(
        ...,
        description="University-issued registration number used as the login identifier.",
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Account password. Verified against the stored bcrypt hash.",
    )


class AdminResetPasswordSchema(BaseModel):
    """
    Payload for POST /api/v1/admin/users/{user_id}/reset-password.
    Admin provides a new temporary password for the user.
    """
    new_password: str = Field(
        ...,
        min_length=12,
        description="New temporary password. Minimum 12 characters.",
    )


class ChangePasswordSchema(BaseModel):
    """
    Payload for POST /auth/change-password.
    Used during onboarding or any time user wants to change their password.
    """
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=12,
        description="New password. Minimum 12 characters.",
    )


# ---------------------------------------------------------------------------
# Response Schemas (Outbound)
# ---------------------------------------------------------------------------


class TokenSchema(BaseModel):
    """
    Response for POST /auth/login on successful authentication.

    token_type is a Literal so the OpenAPI spec documents it as a constant
    and clients cannot accidentally send an incorrect token type.
    """

    access_token: str = Field(
        ...,
        description="Signed JWT access token. Valid for 15 minutes.",
    )
    token_type: Literal["bearer"] = Field(
        default="bearer",
        description="OAuth2 token type. Always 'bearer'.",
    )


class UserResponseSchema(BaseModel):
    """
    Response for POST /auth/register/* and GET /auth/me.

    Returns authenticated user identity data only. No password fields.
    No role-specific profile data (branch, cgpa, department, etc.) —
    those belong to profile management endpoints in a future phase.

    `registration_number` is a direct column on User as of Stage 1 of the
    identity refactor. No service-layer join to Student or Faculty is required
    to populate this field — it is read directly from user.registration_number.

    `from_attributes=True` enables ORM-to-schema conversion via model_validate().
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ...,
        description="User's unique identifier (UUID v4). Serialized as a string in JSON.",
    )
    full_name: str = Field(
        ...,
        description="User's full name.",
    )
    email: str = Field(
        ...,
        description="User's registered email address.",
    )
    role: UserRole = Field(
        ...,
        description="User's role in the platform: 'student', 'faculty', or 'admin'.",
    )
    is_active: bool = Field(
        ...,
        description="Whether the account is active. Inactive accounts cannot log in.",
    )
    registration_number: str = Field(
        ...,
        description=(
            "University-issued registration number. Primary authentication identifier "
            "and business key across all university workflows. Direct column on User."
        ),
    )
    requires_password_change: bool = Field(
        default=False,
        description="Whether the user needs to change their password before proceeding.",
    )
    profile_completed: bool = Field(
        default=False,
        description="Whether the user has completed their profile setup.",
    )
    linkedin_url: Optional[str] = Field(
        default=None,
        description="LinkedIn profile URL (Student only).",
    )
    github_url: Optional[str] = Field(
        default=None,
        description="GitHub profile URL (Student only).",
    )
    portfolio_url: Optional[str] = Field(
        default=None,
        description="Personal portfolio URL (Student only).",
    )
