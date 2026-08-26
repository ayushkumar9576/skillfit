from dotenv import load_dotenv
load_dotenv()  # Must run before any module that reads os.getenv (security.py, database.py)

import app.db.base  # noqa: F401 — registers all ORM models with SQLAlchemy metadata

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.auth import router as auth_router
from app.api.resume import router as resume_router
from app.core.rate_limit import limiter

# NOTE: extraction_router is intentionally NOT registered here.
# POST /resume/{id}/extract and GET /resume/{id}/text are no longer public endpoints.
# Text extraction is triggered automatically as a background task by the upload pipeline.
# See: app/services/resume_pipeline.py — process_resume_pipeline()
# See: app/services/extraction_service.py — extract_resume_internal()

app = FastAPI(
    title="SkillFit API",
    version="3.5.1",
    description=(
        "AI-powered student placement intelligence platform. "
        "Resume processing (extraction, section detection, analysis) runs automatically "
        "as a background pipeline after upload — students only interact with upload "
        "and retrieval endpoints."
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

app.include_router(auth_router)
app.include_router(resume_router)
# extraction_router removed: extraction is now internal-only (Pre-Phase 3.6)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
