"""
app/api/v1/admin_users.py
-------------------------
Admin APIs for User Management.
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.enums import UserRole
from app.models.user import User
from app.schemas.auth import (
    AdminResetPasswordSchema,
    RegisterFacultySchema,
    RegisterStudentSchema,
    UserResponseSchema,
)
from app.services import auth_service

router = APIRouter(prefix="/api/v1/admin/users", tags=["Admin — Users"])

@router.post(
    "/student",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new student account (Admin only)",
)
def create_student(
    data: RegisterStudentSchema,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> UserResponseSchema:
    return auth_service.admin_create_student(db, data)


@router.post(
    "/faculty",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new faculty account (Admin only)",
)
def create_faculty(
    data: RegisterFacultySchema,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> UserResponseSchema:
    return auth_service.admin_create_faculty(db, data)


@router.post(
    "/{user_id}/reset-password",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Reset user password (Admin only)",
)
def reset_password(
    user_id: uuid.UUID,
    data: AdminResetPasswordSchema,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> UserResponseSchema:
    return auth_service.admin_reset_password(db, user_id, data.new_password)
