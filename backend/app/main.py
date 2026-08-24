from dotenv import load_dotenv
load_dotenv()  # Must run before any module that reads os.getenv (security.py, database.py)

import app.db.base  # noqa: F401 — registers all ORM models with SQLAlchemy metadata

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.auth import router as auth_router
from app.api.resume import router as resume_router
from app.api.extraction import router as extraction_router
from app.core.rate_limit import limiter

app = FastAPI(
    title="SkillFit API",
    version="3.3.0",
    description="AI-powered student placement intelligence platform.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(extraction_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
