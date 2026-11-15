"""
app/api/v1/candidate_profile.py
-------------------------------
Candidate Profile API for the Placement Matching Engine.

Returns matching-ready structure combining student eligibility and candidate
profile intelligence derived from the latest active resume intelligence snapshot.
"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.resume_file import ResumeFile
from app.core.enums import UserRole
from app.services.analysis_persistence_service import get_latest_snapshot, get_profile

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

    # Resolve student's latest active resume
    active_resume = (
        db.query(ResumeFile)
        .filter(ResumeFile.student_id == student.id, ResumeFile.is_active == True)
        .order_by(ResumeFile.created_at.desc())
        .first()
    )

    snapshot = get_latest_snapshot(db, active_resume.id) if active_resume else None

    # Derive intelligence from snapshot if available
    primary_domain = None
    secondary_domains: List[str] = []
    strongest_skills: List[str] = []
    normalized_skills: List[str] = []
    soft_skills: List[str] = []
    role_affinities: Dict[str, Any] = {}
    evidence_summary: Dict[str, Any] = {}
    readiness_score = None
    readiness_label = None
    profile_completeness_score = 0

    if snapshot and snapshot.profile_json:
        payload = snapshot.profile_json
        profile_data = payload.get("profile", {})
        summary = profile_data.get("summary", {})

        p_domains = summary.get("primary_domains", [])
        if p_domains:
            primary_domain = p_domains[0]
            secondary_domains = p_domains[1:]

        strongest_skills = summary.get("strongest_technologies", [])
        skills_list = profile_data.get("skills", [])
        normalized_skills = [s.get("skill") for s in skills_list if isinstance(s, dict) and s.get("skill")]
        
        # Soft skills from competencies
        competencies = profile_data.get("competencies", [])
        soft_skills = [
            c.get("competency") for c in competencies
            if isinstance(c, dict) and c.get("competency")
        ]

        # Use the same assessment as the dashboard and CV analysis endpoints.
        profile = get_profile(db, active_resume.id)
        if profile is not None:
            readiness_score = profile.readiness_score
            readiness_label = profile.readiness_level

        findings = profile_data.get("findings", [])

        # Evidence summary
        evidence_summary = {
            "projects_count": len(profile_data.get("project_sophistication", [])),
            "certifications_count": len(profile_data.get("certifications", [])),
            "skills_count": len(skills_list),
            "findings_count": len(findings),
        }
        profile_completeness_score = min(100, int(
            (min(len(skills_list), 10) / 10) * 40 +
            (min(len(profile_data.get("project_sophistication", [])), 3) / 3) * 40 +
            (min(len(profile_data.get("certifications", [])), 2) / 2) * 20
        ))

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
            "primary_domain": primary_domain,
            "secondary_domains": secondary_domains,
            "role_affinities": role_affinities,
            "readiness_score": readiness_score,
            "readiness_label": readiness_label,
            "strongest_skills": strongest_skills,
            "soft_skills": soft_skills,
            "normalized_skills": normalized_skills,
            "profile_completeness_score": profile_completeness_score,
            "evidence_summary": evidence_summary
        },
        "metadata": {
            "analysis_version": snapshot.analysis_version if snapshot else None,
            "generated_at": snapshot.generated_at.isoformat() if snapshot and snapshot.generated_at else None,
            "source_resume_id": str(active_resume.id) if active_resume else None
        }
    }
