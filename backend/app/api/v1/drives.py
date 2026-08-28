"""
app/api/v1/drives.py
--------------------
Drives API for placement matching.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.drive import Drive
from app.analysis.engines.normalization_engine import normalize_skill_name

router = APIRouter(prefix="/api/v1/drives", tags=["Drives"])

class DriveCreateSchema(BaseModel):
    company_name: str
    role: str
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = []
    structured_eligibility: Optional[dict] = {}

@router.post("")
def create_drive(
    data: DriveCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Normalize skills using the same engine as candidate analysis
    normalized_req = [normalize_skill_name(s) for s in data.required_skills]
    normalized_pref = [normalize_skill_name(s) for s in data.preferred_skills] if data.preferred_skills else []
    
    new_drive = Drive(
        company_name=data.company_name,
        role=data.role,
        required_skills=normalized_req,
        preferred_skills=normalized_pref,
        structured_eligibility=data.structured_eligibility
    )
    db.add(new_drive)
    db.commit()
    db.refresh(new_drive)
    return new_drive
