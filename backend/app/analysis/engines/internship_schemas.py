"""
app/analysis/engines/internship_schemas.py
-------------------------------------------
Pydantic v2 validation schemas for the SkillFit Internship Analysis Engine
(Phase 3.8).

These schemas mirror the pure-dataclass report structures in
``app.analysis.models.internship_models`` but live here, in the ``engines``
package, because they are the LLM boundary.

Wire format vs. report shape:
- Uses `ev: List[EvidenceRef]` (line-number references) instead of quoting text to save tokens.
- `skills_and_tech` list acts as a single compact wire array that later fans out to both `TechnologyUsage` and `SkillEvidenceMap`.
"""

from typing import Annotated, Any, List, Optional, Union

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


EvidenceRef = Union[int, str]


def coerce_evidence_refs(value: Any) -> List[EvidenceRef]:
    """
    Normalize whatever the model produced for an ``ev`` field into line refs.
    """
    if value is None:
        return []
    if isinstance(value, (int, str, dict)):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []

    refs: List[EvidenceRef] = []
    for entry in value:
        if isinstance(entry, bool):
            continue
        if isinstance(entry, int):
            refs.append(entry)
            continue
        if isinstance(entry, float) and entry.is_integer():
            refs.append(int(entry))
            continue
        if isinstance(entry, str):
            stripped = entry.strip()
            if not stripped:
                continue
            refs.append(int(stripped) if stripped.lstrip("-").isdigit() else stripped)
            continue
        if isinstance(entry, dict):
            line = entry.get("line", entry.get("line_number"))
            if isinstance(line, bool):
                line = None
            if isinstance(line, int):
                refs.append(line)
                continue
            if isinstance(line, str) and line.strip().lstrip("-").isdigit():
                refs.append(int(line.strip()))
                continue
            text = entry.get("text", entry.get("evidence_text"))
            if isinstance(text, str) and text.strip():
                refs.append(text.strip())
    return refs


EvidenceRefs = Annotated[List[EvidenceRef], BeforeValidator(coerce_evidence_refs)]


class ScoredDimensionSchema(BaseModel):
    """
    A single evidence-backed 0–100 score with reasoning + evidence refs.
    """
    model_config = ConfigDict(extra="ignore")

    score: float = Field(0.0, description="0–100 numeric score; 0 when unsupported.")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = ""
    ev: EvidenceRefs = Field(default_factory=list)


class InternshipUnderstandingSchema(BaseModel):
    """What the internship actually is."""
    model_config = ConfigDict(extra="ignore")

    purpose: Optional[str] = ""
    domain: Optional[str] = ""
    company_type: Optional[str] = ""
    team_function: Optional[str] = ""
    role_objective: Optional[str] = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    ev: EvidenceRefs = Field(default_factory=list)


class WorkplaceMaturitySchema(BaseModel):
    """Classification/score capturing exposure to production systems, etc."""
    model_config = ConfigDict(extra="ignore")

    classification: Optional[str] = ""
    score: float = 0.0
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = ""
    ev: EvidenceRefs = Field(default_factory=list)


class OwnershipClassificationSchema(BaseModel):
    """Classification of ownership (observer, contributor, owner, lead_contributor)."""
    model_config = ConfigDict(extra="ignore")

    classification: Optional[str] = ""
    score: float = 0.0
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = ""
    ev: EvidenceRefs = Field(default_factory=list)


class SkillTechSchema(BaseModel):
    """
    ONE skill-or-technology, carrying both of the facets the report needs.
    """
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field("", description="Technology or skill name.")
    kind: Optional[str] = Field(None, description="'tech' | 'skill'.")
    depth: float = Field(0.0, description="0–100 depth-of-use score.")
    status: Optional[str] = Field("unverified", description="claimed | demonstrated | verified | unverified")
    sophistication: Optional[str] = ""
    understanding: Optional[str] = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = ""
    ev: EvidenceRefs = Field(default_factory=list)


class CompetencySchema(BaseModel):
    """A demonstrated engineering competency."""
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = ""
    score: float = 0.0
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = ""
    ev: EvidenceRefs = Field(default_factory=list)


class AssessedPointSchema(BaseModel):
    """A single strength / weakness / risk with reasoning + evidence refs."""
    model_config = ConfigDict(extra="ignore")

    statement: Optional[str] = ""
    reasoning: Optional[str] = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    ev: EvidenceRefs = Field(default_factory=list)


class MissingEvidenceItemSchema(BaseModel):
    """An expected aspect the resume does not substantiate."""
    model_config = ConfigDict(extra="ignore")

    aspect: Optional[str] = ""
    description: Optional[str] = ""
    impact: Optional[str] = ""


class ExecutiveAssessmentSchema(BaseModel):
    """Executive-level technical summary of the internship."""
    model_config = ConfigDict(extra="ignore")

    overall_impression: Optional[str] = ""
    demonstrates: List[str] = Field(default_factory=list)
    does_not_demonstrate: List[str] = Field(default_factory=list)
    strongest_signals: List[str] = Field(default_factory=list)
    weakest_signals: List[str] = Field(default_factory=list)
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)


class InternshipIntelligence(BaseModel):
    """
    Top-level validated schema for ONE internship's deep intelligence report.
    """
    model_config = ConfigDict(extra="ignore")

    understanding: InternshipUnderstandingSchema = Field(default_factory=InternshipUnderstandingSchema)
    technical_depth: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    engineering_ownership: OwnershipClassificationSchema = Field(default_factory=OwnershipClassificationSchema)
    collaboration_exposure: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    impact_analysis: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    production_exposure: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    software_engineering_practices: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    
    skills_and_tech: List[SkillTechSchema] = Field(default_factory=list)
    competencies: List[CompetencySchema] = Field(default_factory=list)
    
    industry_readiness: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    hiring_signal: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    internship_quality: Optional[str] = ""
    workplace_maturity: WorkplaceMaturitySchema = Field(default_factory=WorkplaceMaturitySchema)
    
    strengths: List[AssessedPointSchema] = Field(default_factory=list)
    weaknesses: List[AssessedPointSchema] = Field(default_factory=list)
    missing_evidence: List[MissingEvidenceItemSchema] = Field(default_factory=list)
    risks: List[AssessedPointSchema] = Field(default_factory=list)
    
    executive_assessment: ExecutiveAssessmentSchema = Field(default_factory=ExecutiveAssessmentSchema)
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)
    caveats: List[str] = Field(default_factory=list)
