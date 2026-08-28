"""
app/api/v1/candidate_profile.py
-------------------------------
Candidate Profile API for the Placement Matching Engine.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.core.enums import UserRole

router = APIRouter(prefix="/api/v1/candidate-profile", tags=["Candidate Profile"])

@router.get("/me", response_model=Dict[str, Any])
def get_my_candidate_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students have a candidate profile."
        )
        
    student = current_user.student
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
        
    cp = student.candidate_profile
    
    # Return matching-ready structure combining student eligibility and candidate profile intelligence
    return {
        "student_id": student.id,
        "eligibility": {
            "branch": student.branch,
            "cgpa": float(student.cgpa) if student.cgpa else None,
            "graduation_year": student.graduation_year,
            "active_backlogs": student.active_backlogs
        },
        "intelligence": {
            "primary_domain": cp.primary_domain if cp else None,
            "secondary_domains": cp.secondary_domains if cp else [],
            "role_affinities": cp.role_affinities if cp else {},
            "readiness_score": float(cp.readiness_score) if cp and cp.readiness_score else None,
            "readiness_label": cp.readiness_label if cp else None,
            "strongest_skills": cp.strongest_skills if cp else [],
            "soft_skills": cp.soft_skills if cp else [],
            "normalized_skills": cp.normalized_skills if cp else [],
            "profile_completeness_score": cp.profile_completeness_score if cp else 0,
            "evidence_summary": cp.evidence_summary if cp else {}
        },
        "metadata": {
            "analysis_version": cp.analysis_version if cp else None,
            "generated_at": cp.generated_at.isoformat() if cp and cp.generated_at else None,
            "source_resume_id": str(cp.source_resume_id) if cp and cp.source_resume_id else None
        }
    }
