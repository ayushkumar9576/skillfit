"""
app/api/v1/profile.py
---------------------
Profile completion and updates API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserResponseSchema
from app.schemas.profile import ProfileUpdateSchema
from app.services import auth_service

router = APIRouter(prefix="/api/v1/profile", tags=["Profile Management"])

@router.put(
    "",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Complete or update user profile",
)
def complete_profile(
    data: ProfileUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponseSchema:
    if current_user.role == UserRole.student:
        if not data.branch or data.cgpa is None or not data.phone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="branch, cgpa, and phone are required for students."
            )
        student = current_user.student
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found.")
        student.branch = data.branch
        student.cgpa = data.cgpa
        student.phone = data.phone
        student.linkedin_url = str(data.linkedin_url) if data.linkedin_url else None
        student.github_url = str(data.github_url) if data.github_url else None
        student.portfolio_url = str(data.portfolio_url) if data.portfolio_url else None
        student.graduation_year = data.graduation_year
        student.active_backlogs = data.active_backlogs
        student.profile_completed = True

    elif current_user.role == UserRole.faculty:
        if not data.department:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="department is required for faculty."
            )
        faculty = current_user.faculty
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty profile not found.")
        faculty.department = data.department
        faculty.profile_completed = True

    else:
        # Admin has no profile completion requirement currently
        pass

    db.commit()
    return auth_service._build_user_response(current_user)
