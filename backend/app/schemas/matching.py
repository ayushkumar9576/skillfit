import uuid
from pydantic import BaseModel, Field
from typing import List, Optional

class DimensionBreakdownDTO(BaseModel):
    dimension: str
    raw_score: float
    weight: float
    weighted_score: float
    matched_items: int = 0
    total_items: int = 0
    reasoning: str = ""
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)

class RecommendedDriveResponse(BaseModel):
    drive_id: uuid.UUID
    drive_title: str
    company_name: Optional[str]
    score: float
    raw_score: Optional[float] = None
    tier: str
    strengths: List[str]
    gaps: List[str]
    overall_narrative: str
    dimension_breakdown: List[DimensionBreakdownDTO] = Field(default_factory=list)

class RecommendedCandidateResponse(BaseModel):
    candidate_id: uuid.UUID
    student_name: str
    score: float
    raw_score: Optional[float] = None
    tier: str
    strengths: List[str]
    gaps: List[str]
    overall_narrative: str
    dimension_breakdown: List[DimensionBreakdownDTO] = Field(default_factory=list)
