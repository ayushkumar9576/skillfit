"""
app/analysis/engines/certification_schemas.py
---------------------------------------------
Pydantic V2 boundary schemas for Phase 3.9 Certification Analysis.

These schemas strictly enforce the LLM's structured output. They use the compact
wire schema optimization (`ev: List[int]`) to minimize token consumption while
retaining line-level evidence traceability.

Consumed by:
    - Phase 3.9: Certification Analysis Engine (via GeminiProvider)
"""

from typing import List, Optional
from pydantic import BaseModel, Field

# Alias for our compact evidence array (just a list of line numbers)
EvidenceRefs = List[int]


class ScoredDimensionSchema(BaseModel):
    """A scored dimension with strict constraints."""
    classification: Optional[str] = Field(None, description="Optional classification if applicable")
    score: int = Field(0, ge=0, le=100, description="0-100 score")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="0.0-1.0 confidence")
    reasoning: str = Field(..., description="Max 20 words reasoning")
    ev: EvidenceRefs = Field(default_factory=list, description="Line number citations")


class SkillSignalSchema(BaseModel):
    """A skill reasonably implied by the certification."""
    name: str = Field(..., description="Name of the skill")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="0.0-1.0 confidence")
    reasoning: str = Field(..., description="Max 20 words reasoning")
    ev: EvidenceRefs = Field(default_factory=list, description="Line number citations")


class ExecutiveAssessmentSchema(BaseModel):
    """Concise executive-level summary."""
    overall_value: str = Field(..., description="Max 25 words")
    strongest_signal: str = Field(..., description="Max 15 words")
    primary_limitation: str = Field(..., description="Max 15 words")


class CertificationIntelligence(BaseModel):
    """
    The structured output for ONE certification analysis.
    This schema explicitly avoids dimensions like Learning Depth or Missing Evidence
    to aggressively minimize token consumption and hallucination.
    """
    certification_recognition: ScoredDimensionSchema
    skill_signals: List[SkillSignalSchema] = Field(default_factory=list, max_length=5)
    industry_relevance: ScoredDimensionSchema
    hiring_signal: ScoredDimensionSchema
    evidence_strength: ScoredDimensionSchema
    executive_assessment: ExecutiveAssessmentSchema
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)
    caveats: List[str] = Field(default_factory=list, max_length=2)


class CertificationBatchIntelligence(BaseModel):
    """
    The root structured output for a batched analysis call.
    Expects up to BATCH_SIZE (e.g. 5) certifications analyzed at once.
    """
    certifications: List[CertificationIntelligence] = Field(default_factory=list)
