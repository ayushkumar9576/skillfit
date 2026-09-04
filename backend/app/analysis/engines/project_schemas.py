"""
app/analysis/engines/project_schemas.py
----------------------------------------
Pydantic v2 LLM boundary schemas for the SkillFit Project Analysis Engine
(Phase 3 Remediation).

Architecture Principle:
    LLM = Structured Qualitative Intelligence
    Python = All Scores, Tiers, Confidence, Rankings

The LLM evaluates:
    - What technologies were demonstrated, and at what level
    - Which competencies are evidenced
    - What ownership signals exist
    - Which engineering signals are present (architecture, deployment, testing, security)
    - Strengths, weaknesses, and missing signals
    - Project sophistication score (holistic 0-100 integer)

The LLM does NOT generate:
    - Confidence percentages
    - Project tiers (these are computed deterministically from the score by Python)
    - Readiness scores
    - Per-dimension sub-scores

Wire format design:
    - Evidence is cited by line number (``ev: [4, 7]``) rather than re-quoting text,
      saving ~33% of output tokens while improving traceability.
    - ``ConfigDict(extra="ignore")`` on all models so a chatty model never breaks parsing.
    - Every field optional-with-default so partial responses still map gracefully.
    - All enumerated values (DemonstrationLevel, CompetencyType, etc.) are plain strings —
      the prompt supplies the allowed vocabulary, the mapper stores verbatim.
"""

from typing import Annotated, Any, Dict, List, Optional, Union

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

# ---------------------------------------------------------------------------
# Evidence reference coercion (unchanged — well-tested and resilient)
# ---------------------------------------------------------------------------

EvidenceRef = Union[int, str]


def coerce_evidence_refs(value: Any) -> List[EvidenceRef]:
    """
    Normalize whatever the model produced for an ``ev`` field into line refs.

    Accepted per entry:
        4                         -> 4          (intended form)
        "4" / " 4 "               -> 4          (stringified number)
        {"line": 4}               -> 4          (over-structured)
        {"text": "Built an API"}  -> "Built an API"   (legacy quote object)
        "Built an API"            -> "Built an API"   (bare quote)
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


# ---------------------------------------------------------------------------
# Project Understanding (qualitative, no scores)
# ---------------------------------------------------------------------------

class UnderstandingSchema(BaseModel):
    """What the project actually is — purpose, domain, and users."""
    model_config = ConfigDict(extra="ignore")

    purpose: Optional[str] = ""
    problem_solved: Optional[str] = ""
    intended_users: Optional[str] = ""
    domain: Optional[str] = ""
    project_type: Optional[str] = ""
    business_value: Optional[str] = ""
    ev: EvidenceRefs = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Technology Intelligence Schema
# ---------------------------------------------------------------------------

class TechnologyIntelligenceSchema(BaseModel):
    """
    ONE technology entry with its demonstration level.

    demonstration_level must be one of:
        CLAIMED | REFERENCED | USED | IMPLEMENTED | DESIGNED | ARCHITECTED
    """
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
    ONE demonstrated engineering competency.

    competency must map to a value from the canonical CompetencyType taxonomy:
        BACKEND_DEVELOPMENT | FRONTEND_DEVELOPMENT | FULL_STACK_DEVELOPMENT |
        MACHINE_LEARNING | DEEP_LEARNING | DATA_SCIENCE | DATA_ENGINEERING |
        DEVOPS | CLOUD_COMPUTING | MLOPS | SYSTEM_DESIGN | SOFTWARE_ARCHITECTURE |
        DATABASE_DESIGN | API_DEVELOPMENT | TESTING | QA_AUTOMATION |
        CYBERSECURITY | MOBILE_DEVELOPMENT | DISTRIBUTED_SYSTEMS | PROBLEM_SOLVING
    """
    model_config = ConfigDict(extra="ignore")

    competency: Optional[str] = Field("", description="CompetencyType value.")
    demonstrated: bool = Field(True, description="True if evidence strongly supports this competency.")
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
    ONE ownership or leadership signal extracted from the project.

    ownership_level must be one of:
        OBSERVED | CONTRIBUTED | IMPLEMENTED | OWNED | LED
    """
    model_config = ConfigDict(extra="ignore")

    signal: Optional[str] = Field("", description="Short description of what was owned/built/led.")
    ownership_level: Optional[str] = Field(
        "CONTRIBUTED",
        description="OBSERVED | CONTRIBUTED | IMPLEMENTED | OWNED | LED"
    )
    ev: EvidenceRefs = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Engineering Signal Schemas
# ---------------------------------------------------------------------------

class EngineeringSignalSchema(BaseModel):
    """
    ONE engineering practice or pattern detected in the project.

    category must be one of: ARCHITECTURE | DEPLOYMENT | TESTING | SECURITY
    """
    model_config = ConfigDict(extra="ignore")

    category: Optional[str] = Field(
        "",
        description="ARCHITECTURE | DEPLOYMENT | TESTING | SECURITY"
    )
    signal: Optional[str] = Field("", description="Short signal description.")
    demonstrated: bool = Field(True, description="True if at least one evidence line supports this signal.")
    ev: EvidenceRefs = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Sophistication Assessment Schema
# ---------------------------------------------------------------------------

class SophisticationAssessmentSchema(BaseModel):
    """
    Holistic project sophistication assessment.

    The LLM produces:
        - sophistication_score: integer 0-100 representing overall project
          maturity and engineering complexity.
        - sophistication_reasoning: concise justification (≤ 30 words).

    The Python engine deterministically derives:
        - sophistication_tier from the score (BEGINNER … INDUSTRY_GRADE).

    Scale:
        0-20:   Tutorial, classroom exercise, or introductory implementation.
        21-40:  Basic CRUD application or simple academic project.
                Limited architecture, integrations, or technical depth.
        41-60:  Intermediate project with multiple interacting components.
                Demonstrates independent problem-solving and moderate engineering complexity.
        61-75:  Advanced engineering project demonstrating substantial technical depth.
                May include machine learning, distributed systems, advanced algorithms,
                simulation, optimization, or significant full-stack implementation.
        76-85:  Production-oriented system demonstrating deployment, automation,
                scalability considerations, monitoring, CI/CD, infrastructure,
                integrations, versioning, security, or operational concerns.
        86-95:  Near-industry system demonstrating strong architecture,
                reliability, maintainability, extensibility, testing strategy,
                and mature engineering practices.
        96-100: Exceptional industry-grade implementation.
                Reserved for rare projects with outstanding architectural sophistication,
                production maturity, operational excellence, and substantial real-world impact.
    """
    model_config = ConfigDict(extra="ignore")

    sophistication_score: int = Field(
        50,
        ge=0,
        le=100,
        description="Overall project sophistication score (0-100)."
    )
    sophistication_reasoning: Optional[str] = Field(
        "",
        description="Concise justification for the score (<= 30 words)."
    )


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

class ProjectIntelligence(BaseModel):
    """
    Top-level validated LLM boundary schema for ONE project's intelligence.

    The LLM evaluates technologies, competencies, ownership, engineering
    signals qualitatively, and provides a holistic sophistication score.

    Every field is optional-with-default so a partial response still maps
    gracefully — a missing dimension is better than a discarded analysis.

    evidence_registry:
        Keys are line numbers from the numbered evidence payload.
        Values carry the evidence type classification for the aggregator.
        Example: {12: {"type": "DIRECT_IMPLEMENTATION"}}
    """
    model_config = ConfigDict(extra="ignore")

    evidence_registry: Dict[int, Dict[str, str]] = Field(
        default_factory=dict,
        description="Line-number → evidence classification map."
    )
    understanding: UnderstandingSchema = Field(default_factory=UnderstandingSchema)
    technologies: List[TechnologyIntelligenceSchema] = Field(
        default_factory=list,
        description="All technologies with demonstration level."
    )
    competencies: List[CompetencyIntelligenceSchema] = Field(
        default_factory=list,
        description="Engineering competencies with evidence."
    )
    ownership_signals: List[OwnershipSignalSchema] = Field(
        default_factory=list,
        description="Ownership and leadership signals."
    )
    engineering_signals: List[EngineeringSignalSchema] = Field(
        default_factory=list,
        description="Architecture, deployment, testing, and security signals."
    )
    findings: List[FindingSchema] = Field(
        default_factory=list,
        description="Strengths, weaknesses, and missing signals. No Recommendations — those are generated by Python."
    )
    sophistication: SophisticationAssessmentSchema = Field(
        default_factory=SophisticationAssessmentSchema,
        description="Holistic project sophistication assessment (score 0-100 + reasoning)."
    )
    caveats: List[str] = Field(default_factory=list)
