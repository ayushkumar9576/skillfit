"""
app/api/v1/dashboards.py
------------------------
Dashboard aggregation endpoints for Phase 3.14.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_user, get_db, require_roles, require_onboarding_completed
from app.core.enums import ProcessingStatus, UserRole
from app.models.user import User
from app.models.student import Student
from app.models.faculty import Faculty
from app.models.resume_file import ResumeFile
from app.models.cv_analysis import CVAnalysis
from app.models.student_skill import StudentSkill
from app.models.student_project import StudentProject
from app.models.student_internship import StudentInternship
from app.models.certification import Certification
from app.schemas.dashboard import StudentDashboardSchema, AdminDashboardSchema, FacultyDashboardSchema
from app.services import resume_service

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
            data["analysis_available"] = True
            cv = db.query(CVAnalysis).filter(CVAnalysis.resume_id == resume.id).first()
            if cv:
                data["readiness_level"] = cv.readiness_level
            
            data["skills_count"] = db.query(StudentSkill).filter(StudentSkill.resume_id == resume.id).count()
            data["projects_count"] = db.query(StudentProject).filter(StudentProject.resume_id == resume.id).count()
            data["internships_count"] = db.query(StudentInternship).filter(StudentInternship.resume_id == resume.id).count()
            data["certifications_count"] = db.query(Certification).filter(Certification.resume_id == resume.id).count()

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
