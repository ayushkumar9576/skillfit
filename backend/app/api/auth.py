"""
app/api/auth.py
---------------
FastAPI route handlers for SkillFit Phase 2 authentication.

Endpoints:
    POST /auth/register/student  — Register a new student account
    POST /auth/register/faculty  — Register a new faculty account
    POST /auth/login             — Login with email + password, receive JWT
    GET  /auth/me                — Return the current authenticated user's identity

Design:
    - Route handlers are intentionally thin. All business logic lives in
      app/services/auth_service.py.
    - Authentication is enforced via the get_current_user dependency from
      app/api/deps.py.
    - Response models are declared explicitly on each route so FastAPI
      generates accurate OpenAPI schemas and filters unexpected fields.
"""

from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import (
    LoginSchema,
    RegisterFacultySchema,
    RegisterStudentSchema,
    TokenSchema,
    UserResponseSchema,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])



@router.post(
    "/register/student",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account",
    description=(
        "Creates a User (role=student) and a linked Student profile row. "
        "Returns the new user's identity data including their registration number."
    ),
)
@limiter.limit("10/hour")
def register_student(
    request: Request,
    data: RegisterStudentSchema,
    db: Session = Depends(get_db),
) -> UserResponseSchema:
    return auth_service.register_student(db, data)


@router.post(
    "/register/faculty",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new faculty account",
    description=(
        "Creates a User (role=faculty) and a linked Faculty profile row. "
        "Returns the new user's identity data including their registration number."
    ),
)
@limiter.limit("10/hour")
def register_faculty(
    request: Request,
    data: RegisterFacultySchema,
    db: Session = Depends(get_db),
) -> UserResponseSchema:
    return auth_service.register_faculty(db, data)



@router.post(
    "/login",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    summary="Login and receive a JWT access token (JSON)",
    description=(
        "Authenticates the user by registration_number and password via JSON payload. "
        "Returns a signed JWT Bearer token valid for 15 minutes."
    ),
)
@limiter.limit("5/15minute")
def login(
    request: Request,
    data: LoginSchema,
    db: Session = Depends(get_db),
) -> TokenSchema:
    return auth_service.login_user(db, data)


@router.post(
    "/token",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 Password token endpoint (Swagger UI & OAuth2 clients)",
    description=(
        "Authenticates via OAuth2 password flow form-data (username=registration_number or email, password). "
        "Used natively by Swagger UI's Authorize dialog."
    ),
)
@limiter.limit("5/15minute")
def login_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenSchema:
    return auth_service.login_oauth2(
        db=db,
        username=form_data.username,
        password=form_data.password,
    )



@router.get(
    "/me",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Get the current authenticated user",
    description=(
        "Returns the authenticated user's identity data. "
        "Requires a valid JWT Bearer token in the Authorization header."
    ),
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponseSchema:
    """
    Return the authenticated user's identity.

    registration_number is now a direct column on User (Stage 1 identity
    refactor) — no role-based branching required.
    """
    return UserResponseSchema(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        registration_number=current_user.registration_number,
    )
