from dotenv import load_dotenv
load_dotenv()  # Must run before any module that reads os.getenv (security.py, database.py)

import app.db.base  # noqa: F401 — registers all ORM models with SQLAlchemy metadata

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.auth import router as auth_router
from app.api.resume import router as resume_router
from app.api.v1.student_resumes import router as student_resumes_router
from app.api.v1.admin_resumes import router as admin_resumes_router
from app.api.v1.admin_users import router as admin_users_router
from app.api.v1.admin_import import router as admin_import_router
from app.api.v1.profile import router as profile_router
from app.api.v1.drives import router as drives_router
from app.api.v1.candidate_profile import router as candidate_profile_router
from app.api.v1.dashboards import student_router as student_dashboard_router, admin_router as admin_dashboard_router, faculty_router as faculty_dashboard_router
from app.core.rate_limit import limiter

# NOTE: extraction_router is intentionally NOT registered here.
# POST /resume/{id}/extract and GET /resume/{id}/text are no longer public endpoints.
# Text extraction is triggered automatically as a background task by the upload pipeline.
# See: app/services/resume_pipeline.py — process_resume_pipeline()
# See: app/services/extraction_service.py — extract_resume_internal()

app = FastAPI(
    title="SkillFit API",
    version="4.1.0",
    description=(
        "AI-powered student placement intelligence platform. "
        "Resume processing (extraction, section detection, analysis) is triggered manually "
        "by Admins via POST /api/v1/admin/resumes/{id}/analyze after a student uploads. "
        "Students view analysis results via GET /api/v1/resumes/{id}/readiness etc."
    ),
)

# ---------------------------------------------------------------------------
# CORS — Allow the Next.js frontend (localhost:3000) to call this API.
# In production, replace the origin with the deployed frontend domain.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Legacy routes (Phase 3.2 – 3.12, kept for backward compatibility)
app.include_router(auth_router)
app.include_router(resume_router)

# Phase 3.13 — versioned REST API
app.include_router(student_resumes_router)
app.include_router(admin_resumes_router)

# Phase 3.14 — Onboarding & Dashboards
app.include_router(admin_users_router)
app.include_router(admin_import_router)
app.include_router(profile_router)
app.include_router(student_dashboard_router)
app.include_router(admin_dashboard_router)
app.include_router(faculty_dashboard_router)
app.include_router(candidate_profile_router)

# Phase 4.1 — Drive Intelligence Foundation
# drives_router now includes Drive CRUD, lifecycle management, and snapshot retrieval.
app.include_router(drives_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
