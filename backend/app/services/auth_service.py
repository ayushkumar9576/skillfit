"""
app/services/auth_service.py
-----------------------------
Business logic for SkillFit Phase 2 authentication.

Handles:
    - Student registration
    - Faculty registration
    - Login (registration_number + password)

What this module does NOT do:
    - HTTP request/response handling (that belongs in app/api/auth.py)
    - JWT logic (that belongs in app/core/security.py)
    - Schema validation (Pydantic handles that before the service is called)

Error conventions:
    - Raises fastapi.HTTPException directly so that route handlers stay thin.
    - 409 Conflict  — duplicate email or registration_number
    - 401 Unauthorized — invalid credentials or inactive account
    - 500 (via unhandled exception) — unexpected DB errors bubble up naturally

Stage 1 identity refactor:
    User.registration_number is now the primary identity field and login
    credential. registration_number is written to both User AND Student/Faculty
    during Stage 1 (two-phase migration) to allow side-by-side verification.
    Stage 2 will remove the legacy Student/Faculty columns.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import create_access_token, hash_password, verify_password
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.user import User
from app.schemas.auth import (
    LoginSchema,
    RegisterFacultySchema,
    RegisterStudentSchema,
    TokenSchema,
    UserResponseSchema,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_user_response(user: User) -> UserResponseSchema:
    """
    Construct a UserResponseSchema from a User ORM object.

    registration_number is now a direct column on User (Stage 1 refactor),
    so no separate lookup against Student or Faculty is required.

    Called after registration and by /auth/me.
    """
    return UserResponseSchema(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        registration_number=user.registration_number,
    )


def _check_email_unique(db: Session, email: str) -> None:
    """Raise 409 if the email is already registered."""
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )


def _check_registration_number_unique(db: Session, registration_number: str) -> None:
    """Raise 409 if the registration number is already registered on User."""
    existing = db.query(User).filter(
        User.registration_number == registration_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This registration number is already registered.",
        )


# ---------------------------------------------------------------------------
# Student Registration
# ---------------------------------------------------------------------------


def register_student(db: Session, data: RegisterStudentSchema) -> UserResponseSchema:
    """
    Register a new student account.

    Creates a User row (role=student) and a linked Student row atomically.
    registration_number is stored on User (authoritative) AND on Student
    (Stage 1 two-phase migration — legacy column retained for verification).
    Returns a UserResponseSchema on success.

    Raises:
        HTTPException 409 — duplicate email or registration_number.
    """
    _check_email_unique(db, data.email)
    _check_registration_number_unique(db, data.registration_number)

    user = User(
        id=uuid.uuid4(),
        full_name=data.full_name,
        email=data.email,
        registration_number=data.registration_number,   # authoritative location
        password_hash=hash_password(data.password),
        role=UserRole.student,
    )

    student = Student(
        user=user,
        registration_number=data.registration_number,   # Stage 1: legacy column retained
        branch=data.branch,
        cgpa=data.cgpa,
        phone=data.phone,
    )

    db.add(user)
    db.add(student)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig).lower() if e.orig else str(e).lower()
        if "email" in error_msg:
            detail = "An account with this email address already exists."
        elif "registration_number" in error_msg:
            detail = "Registration number is already in use."
        else:
            detail = "An account with the provided details already exists."
            
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    db.refresh(user)
    return _build_user_response(user)


# ---------------------------------------------------------------------------
# Faculty Registration
# ---------------------------------------------------------------------------


def register_faculty(db: Session, data: RegisterFacultySchema) -> UserResponseSchema:
    """
    Register a new faculty account.

    Creates a User row (role=faculty) and a linked Faculty row atomically.
    registration_number is stored on User (authoritative) AND on Faculty
    (Stage 1 two-phase migration — legacy column retained for verification).
    Returns a UserResponseSchema on success.

    Raises:
        HTTPException 409 — duplicate email or registration_number.
    """
    _check_email_unique(db, data.email)
    _check_registration_number_unique(db, data.registration_number)

    user = User(
        id=uuid.uuid4(),
        full_name=data.full_name,
        email=data.email,
        registration_number=data.registration_number,   # authoritative location
        password_hash=hash_password(data.password),
        role=UserRole.faculty,
    )

    faculty = Faculty(
        user=user,
        registration_number=data.registration_number,   # Stage 1: legacy column retained
        department=data.department,
    )

    db.add(user)
    db.add(faculty)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig).lower() if e.orig else str(e).lower()
        if "email" in error_msg:
            detail = "An account with this email address already exists."
        elif "registration_number" in error_msg:
            detail = "Registration number is already in use."
        else:
            detail = "An account with the provided details already exists."
            
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    db.refresh(user)
    return _build_user_response(user)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


def login_user(db: Session, data: LoginSchema) -> TokenSchema:
    """
    Authenticate a user by registration_number and password.

    Updates last_login_at on successful login.
    Returns a TokenSchema containing a signed JWT access token.

    Raises:
        HTTPException 401 — invalid credentials or inactive account.

    Note:
        The error message is intentionally generic ("Invalid credentials")
        regardless of whether the registration_number does not exist or the
        password is wrong. This prevents user-enumeration attacks.
    """
    _INVALID_CREDENTIALS = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user: User | None = db.query(User).filter(
        User.registration_number == data.registration_number
    ).first()

    if not user:
        raise _INVALID_CREDENTIALS

    if not verify_password(data.password, user.password_hash):
        raise _INVALID_CREDENTIALS

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return TokenSchema(access_token=token)


def login_oauth2(db: Session, username: str, password: str) -> TokenSchema:
    """
    Authenticate an OAuth2 password grant request (used by Swagger UI & OAuth2 clients).

    Matches 'username' against registration_number or email for maximum convenience.
    Updates last_login_at on success and returns a TokenSchema with JWT.
    """
    _INVALID_CREDENTIALS = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user: User | None = db.query(User).filter(
        (User.registration_number == username) | (User.email == username)
    ).first()

    if not user:
        raise _INVALID_CREDENTIALS

    if not verify_password(password, user.password_hash):
        raise _INVALID_CREDENTIALS

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account has been deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return TokenSchema(access_token=token)
