"""
app/schemas/dashboard.py
------------------------
Schemas for dashboard aggregation endpoints.
"""

from pydantic import BaseModel
from typing import Optional

class StudentDashboardSchema(BaseModel):
    profile_completed: bool
    resume_id: Optional[str] = None
    resume_type: Optional[str] = None
    processing_status: Optional[str] = None
    readiness_level: Optional[str] = None
    analysis_available: bool
    skills_count: int = 0
    projects_count: int = 0
    internships_count: int = 0
    certifications_count: int = 0

class AdminDashboardSchema(BaseModel):
    total_students: int
    total_faculty: int
    uploaded_resumes: int
    processing_resumes: int
    completed_resumes: int
    failed_resumes: int

class FacultyDashboardSchema(BaseModel):
    profile_completed: bool
    department: Optional[str] = None
