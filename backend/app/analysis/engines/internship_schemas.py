"""
app/analysis/engines/internship_schemas.py
-------------------------------------------
Pydantic v2 LLM boundary schemas for the SkillFit Internship Analysis Engine
(Phase 3 Remediation).

Architecture Principle:
    LLM = Structured Qualitative Intelligence
    Python = All Scores, Tiers, Confidence, Rankings

The LLM evaluates:
    - What workplace exposure is demonstrated (Agile, CI/CD, Production, etc.)
    - Which competencies are evidenced
    - What ownership signals exist
    - What engineering signals are present
    - Findings (strengths, weaknesses, missing signals)

The LLM does NOT generate:
    - Numerical scores
    - Confidence percentages
    - Internship tiers
    - Readiness scores
"""

from typing import Annotated, Any, List, Optional, Union

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

# ---------------------------------------------------------------------------
# Evidence reference coercion
# ---------------------------------------------------------------------------

EvidenceRef = Union[int, str]


def coerce_evidence_refs(value: Any) -> List[EvidenceRef]:
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


# ---------------------------------------------------------------------------
# Technology Intelligence Schema
# ---------------------------------------------------------------------------

class TechnologyIntelligenceSchema(BaseModel):
    """ONE technology used during the internship with its demonstration level."""
    model_config = ConfigDict(extra="ignore")

    technology: Optional[str] = Field("", description="Normalized technology name.")
    demonstration_level: Optional[str] = Field(
        "CLAIMED",
        description="CLAIMED | REFERENCED | USED | IMPLEMENTED | DESIGNED | ARCHITECTED"
    )
    reasoning: Optional[str] = ""
    ev: EvidenceRefs = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Competency Intelligence Schema
# ---------------------------------------------------------------------------

class CompetencyIntelligenceSchema(BaseModel):
    """
    ONE demonstrated engineering competency from the internship.

    competency must map to a value from the canonical CompetencyType taxonomy.
    """
    model_config = ConfigDict(extra="ignore")

    competency: Optional[str] = Field("", description="CompetencyType value.")
    demonstrated: bool = True
    demonstration_level: Optional[str] = Field(
        "USED",
        description="CLAIMED | REFERENCED | USED | IMPLEMENTED | DESIGNED | ARCHITECTED"
    )
    supporting_technologies: List[str] = Field(default_factory=list)
    reasoning: Optional[str] = ""
    ev: EvidenceRefs = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Ownership Signal Schema
# ---------------------------------------------------------------------------

class OwnershipSignalSchema(BaseModel):
    """
    ONE ownership or leadership signal from the internship.

    ownership_level must be one of: OBSERVED | CONTRIBUTED | IMPLEMENTED | OWNED | LED
    """
    model_config = ConfigDict(extra="ignore")

    signal: Optional[str] = ""
    ownership_level: Optional[str] = Field(
        "CONTRIBUTED",
        description="OBSERVED | CONTRIBUTED | IMPLEMENTED | OWNED | LED"
    )
    ev: EvidenceRefs = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Workplace Exposure Schema
# ---------------------------------------------------------------------------

class WorkplaceExposureSchema(BaseModel):
    """
    ONE workplace process or environment the candidate was exposed to.

    Examples: Agile, Code Reviews, CI/CD, Production Systems, Monitoring, On-call
    """
    model_config = ConfigDict(extra="ignore")

    exposure_type: Optional[str] = Field("", description="Normalized workplace exposure label.")
    ev: EvidenceRefs = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Engineering Signal Schema
# ---------------------------------------------------------------------------

class EngineeringSignalSchema(BaseModel):
    """
    ONE engineering practice or pattern observed during the internship.

    category must be one of: ARCHITECTURE | DEPLOYMENT | TESTING | SECURITY
    """
    model_config = ConfigDict(extra="ignore")

    category: Optional[str] = Field(
        "",
        description="ARCHITECTURE | DEPLOYMENT | TESTING | SECURITY"
    )
    signal: Optional[str] = ""
    demonstrated: bool = True
    ev: EvidenceRefs = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Finding Schema
# ---------------------------------------------------------------------------

class FindingSchema(BaseModel):
    """
    A qualitative finding — STRENGTH, WEAKNESS, or MISSING_SIGNAL.

    type must be one of: STRENGTH | WEAKNESS | MISSING_SIGNAL
    severity must be one of: LOW | MEDIUM | HIGH | CRITICAL
    """
    model_config = ConfigDict(extra="ignore")

    type: Optional[str] = Field("", description="STRENGTH | WEAKNESS | MISSING_SIGNAL")
    severity: Optional[str] = Field("MEDIUM", description="LOW | MEDIUM | HIGH | CRITICAL")
    title: Optional[str] = ""
    description: Optional[str] = ""
    ev: EvidenceRefs = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level LLM schema
# ---------------------------------------------------------------------------

class InternshipIntelligence(BaseModel):
    """
    Top-level validated LLM boundary schema for ONE internship's intelligence.

    The LLM evaluates workplace exposure, technologies, competencies, ownership,
    and engineering signals qualitatively. It does NOT generate scores or tiers.
    """
    model_config = ConfigDict(extra="ignore")

    evidence_registry: dict = Field(
        default_factory=dict,
        description="Line-number → evidence classification map."
    )
    technologies: List[TechnologyIntelligenceSchema] = Field(default_factory=list)
    competencies: List[CompetencyIntelligenceSchema] = Field(default_factory=list)
    ownership_signals: List[OwnershipSignalSchema] = Field(default_factory=list)
    workplace_exposure: List[WorkplaceExposureSchema] = Field(default_factory=list)
    engineering_signals: List[EngineeringSignalSchema] = Field(default_factory=list)
    findings: List[FindingSchema] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)
