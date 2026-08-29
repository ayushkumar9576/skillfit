"""
app/api/v1/dashboards.py
------------------------
Dashboard aggregation endpoints — Phase 3.13B.

All intelligence data is now derived from CandidateIntelligenceSnapshot.
Zero runtime reads from legacy tables (CVAnalysis, StudentSkill, etc.).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles, require_onboarding_completed
from app.core.enums import ProcessingStatus, UserRole
from app.models.user import User
from app.models.student import Student
from app.models.faculty import Faculty
from app.models.resume_file import ResumeFile
from app.schemas.dashboard import StudentDashboardSchema, AdminDashboardSchema, FacultyDashboardSchema
from app.services import resume_service
from app.services.analysis_persistence_service import get_profile

student_router = APIRouter(prefix="/api/v1/student/dashboard", tags=["Dashboards"])
admin_router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["Dashboards"])
faculty_router = APIRouter(prefix="/api/v1/faculty/dashboard", tags=["Dashboards"])

@student_router.get("", response_model=StudentDashboardSchema)
def get_student_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student)),
    _: User = Depends(require_onboarding_completed),
):
    student = current_user.student
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Get latest resume
    resume = (
        db.query(ResumeFile)
        .filter(ResumeFile.student_id == student.id)
        .order_by(ResumeFile.created_at.desc())
        .first()
    )

    data = {
        "profile_completed": student.profile_completed,
        "analysis_available": False
    }

    if resume:
        data["resume_id"] = str(resume.id)
        data["resume_type"] = resume.resume_type.value
        data["processing_status"] = resume.processing_status.value

        if resume.processing_status == ProcessingStatus.completed:
            # Load from CandidateIntelligenceSnapshot — zero legacy table reads
            profile = get_profile(db, resume.id)
            if profile:
                data["analysis_available"] = True
                data["skills_count"] = len(profile.skills)
                data["projects_count"] = profile.metadata.total_projects_analyzed
                data["internships_count"] = profile.metadata.total_internships_analyzed
                data["certifications_count"] = profile.metadata.total_certifications_analyzed

                # Derive readiness level from profile findings
                critical_or_high = [
                    f for f in profile.findings
                    if f.severity in ("HIGH", "CRITICAL")
                ]
                gap_findings = [
                    f for f in profile.findings
                    if f.type == "MISSING_SIGNAL"
                ]
                if not critical_or_high and not gap_findings:
                    data["readiness_level"] = "placement_ready"
                elif len(critical_or_high) <= 2:
                    data["readiness_level"] = "moderately_ready"
                else:
                    data["readiness_level"] = "needs_improvement"

    return StudentDashboardSchema(**data)

@admin_router.get("", response_model=AdminDashboardSchema)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    total_students = db.query(Student).count()
    total_faculty = db.query(Faculty).count()

    queue_summary = resume_service.get_queue_summary(db)

    return AdminDashboardSchema(
        total_students=total_students,
        total_faculty=total_faculty,
        uploaded_resumes=queue_summary["uploaded"],
        processing_resumes=queue_summary["processing"],
        completed_resumes=queue_summary["completed"],
        failed_resumes=queue_summary["failed"],
    )

@faculty_router.get("", response_model=FacultyDashboardSchema)
def get_faculty_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.faculty)),
    _: User = Depends(require_onboarding_completed),
):
    faculty = current_user.faculty
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty profile not found")

    return FacultyDashboardSchema(
        profile_completed=faculty.profile_completed,
        department=faculty.department,
    )
