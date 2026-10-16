import uuid
from pydantic import BaseModel
from typing import List, Optional

class RecommendedDriveResponse(BaseModel):
    drive_id: uuid.UUID
    drive_title: str
    company_name: Optional[str]
    score: float
    tier: str
    strengths: List[str]
    gaps: List[str]
    overall_narrative: str

class RecommendedCandidateResponse(BaseModel):
    candidate_id: uuid.UUID
    student_name: str
    score: float
    tier: str
    strengths: List[str]
    gaps: List[str]
    overall_narrative: str
