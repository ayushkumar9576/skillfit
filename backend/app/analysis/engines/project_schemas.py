"""
app/analysis/engines/project_schemas.py
----------------------------------------
Pydantic v2 validation schemas for the SkillFit Project Analysis Engine
(Phase 3.7).

These schemas mirror the pure-dataclass report structures in
``app.analysis.models.project_models`` but live here, in the ``engines``
package, because they are the **LLM boundary** — the model returns JSON, this
layer validates it, and :class:`ProjectAnalysisEngine` maps the validated
result onto the framework-free dataclasses. (The dataclass package forbids
Pydantic imports; this package does not.)

Wire format vs. report shape
============================
This is the **wire** schema, deliberately much smaller than the report it
produces. Anything the engine can reconstruct is NOT transmitted, because every
transmitted character is a billed output token that the model must also spend
time generating:

    Omitted from the wire        Reconstructed by the mapper from
    -------------------------    ---------------------------------------------
    ``max_score``                the constant 100.0
    ``confidence_level``         ``confidence`` via ``_confidence_band()``
    ``source_section``           the constant ``"projects"``
    evidence quote text          the line index (see below)
    skill claimed/…/unverified   grouping ``skills_and_tech`` by ``status``
    ``technology_usage``         the same ``skills_and_tech`` entries

Evidence is cited BY LINE REFERENCE, not by value
-------------------------------------------------
The user message sends line-numbered evidence (``evidence[].line``), so a
finding cites ``"ev": [4, 7]`` instead of re-quoting the resume text. The engine
rehydrates the quote, context snippet, and line number from its own index.

This is the single biggest output saving: the previous format required a full
``{"text": ..., "source_section": ..., "confidence": ...}`` object on each of
~56 scored objects, which meant re-typing the same handful of resume lines ~56
times for zero added information. It also *improves* traceability — a line
number cannot be a paraphrase or a fabricated quote, and an unresolvable
reference is detectable, whereas a hallucinated quote is not.

Validation philosophy (mirrors ``app/services/llm/schemas.py``):
    - ``ConfigDict(extra="ignore")`` everywhere — a chatty model that adds keys
      is tolerated, not rejected.
    - Almost every field is **optional-with-default**, so a slightly incomplete
      report (a missing dimension, an empty list) still validates and is mapped,
      rather than the whole project's analysis being discarded. ``LLMResponseError``
      is non-retryable, so tolerant validation is what keeps partial-but-useful
      reports alive.
    - Omission is meaningful and *encouraged*: the prompt tells the model to omit
      a dimension it cannot support rather than emit a verbose
      "cannot be verified" placeholder. The defaults here (score 0.0,
      confidence 0.0) map to a ``cannot_verify`` band, which is exactly the
      intended reading.
    - Classification / verification values are plain strings (not enums): the
      prompt tells the model the allowed vocabulary, and the mapping layer stores
      them verbatim. This avoids dropping a whole report over a cosmetic value
      mismatch like ``"Production-Like"`` vs ``"production_like"``.
    - Evidence references are coerced tolerantly (see :func:`coerce_evidence_refs`)
      so a model that reverts to quoting text degrades gracefully instead of
      losing the report.
"""

from typing import Annotated, Any, List, Optional, Union

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

#: One evidence citation as it arrives on the wire: either a line number into the
#: payload's ``raw_evidence`` (the intended form) or a raw quote string (the
#: tolerated fallback when a model ignores the line-reference instruction).
EvidenceRef = Union[int, str]


def coerce_evidence_refs(value: Any) -> List[EvidenceRef]:
    """
    Normalize whatever the model produced for an ``ev`` field into line refs.

    The prompt asks for ``[4, 7]``, but tolerance here is what keeps a whole
    report alive when a model improvises. Accepted per entry:

        4                          -> 4          (the intended form)
        "4" / " 4 "                -> 4          (stringified number)
        {"line": 4}                -> 4          (over-structured)
        {"text": "Built an API"}   -> "Built an API"   (legacy quote object)
        "Built an API"             -> "Built an API"   (bare quote)

    A bare int/str that was not wrapped in a list is promoted to a
    single-element list. Unusable entries are dropped rather than raising, so one
    malformed citation never invalidates the finding that carries it.

    Returns:
        A list of ints (line references) and/or non-empty strings (verbatim
        quotes). The engine resolves ints against its line index and passes
        strings through as evidence text.
    """
    if value is None:
        return []
    # A model that emitted a single ref instead of a list.
    if isinstance(value, (int, str, dict)):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []

    refs: List[EvidenceRef] = []
    for entry in value:
        # bool is an int subclass; a stray True/False is not a line number.
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
            # "7" is a line reference; anything else is a verbatim quote.
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


#: Annotated list type used for every ``ev`` field in this module.
EvidenceRefs = Annotated[List[EvidenceRef], BeforeValidator(coerce_evidence_refs)]


class ScoredDimensionSchema(BaseModel):
    """
    A single evidence-backed 0–100 score with reasoning + evidence refs.

    ``max_score`` and ``confidence_level`` are intentionally absent — the mapper
    supplies the former (always 100.0) and derives the latter from ``confidence``.
    """

    model_config = ConfigDict(extra="ignore")

    score: float = Field(0.0, description="0–100 numeric score; 0 when unsupported.")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reasoning: Optional[str] = ""
    ev: EvidenceRefs = Field(
        default_factory=list,
        description="Line numbers from evidence[].line supporting this score.",
    )


class UnderstandingSchema(BaseModel):
    """What the project actually is."""

    model_config = ConfigDict(extra="ignore")

    purpose: Optional[str] = ""
    problem_solved: Optional[str] = ""
    intended_users: Optional[str] = ""
    domain: Optional[str] = ""
    project_type: Optional[str] = ""
    business_value: Optional[str] = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    ev: EvidenceRefs = Field(default_factory=list)


class ArchitectureFacetSchema(BaseModel):
    """Assessment of one architectural area (frontend/backend/db/system_design)."""

    model_config = ConfigDict(extra="ignore")

    area: Optional[str] = ""
    assessment: Optional[str] = ""
    score: float = 0.0
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    ev: EvidenceRefs = Field(default_factory=list)


class ComplexitySchema(BaseModel):
    """
    Multi-dimensional complexity — each facet an independent scored dimension.

    Facets the evidence cannot support should be **omitted** by the model; the
    defaults below then map to score 0 / ``cannot_verify``, which is the correct
    reading and costs no output tokens.
    """

    model_config = ConfigDict(extra="ignore")

    overall: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    backend: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    frontend: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    database: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    system_design: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    integration: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    deployment: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)


class SkillTechSchema(BaseModel):
    """
    ONE skill-or-technology, carrying both of the facets the report needs.

    The report exposes two views of the same entities — ``technology_usage``
    (how deeply a technology was used) and ``skill_evidence.items`` (whether a
    skill is claimed / demonstrated / verified). Asking the model for them
    separately meant analyzing every technology twice, which was ~33% of the
    output and let the two verdicts silently contradict each other.

    So the wire carries one entry per skill/technology and the mapper fans it out
    into both report structures. The dataclass shape is unchanged.

    ``kind`` decides whether the entry ALSO becomes a ``technology_usage`` row.
    It is optional: when absent the engine infers it by matching ``name``
    against the project's extracted technology list. Every entry — technology or
    not — always becomes a ``skill_evidence`` item, so nothing is lost.
    """

    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field("", description="Technology or skill name.")
    kind: Optional[str] = Field(
        None,
        description="'tech' | 'skill'. Optional — inferred from the project's "
                    "technology list when omitted.",
    )
    depth: float = Field(0.0, description="0–100 depth-of-use score.")
    status: Optional[str] = Field(
        "unverified", description="claimed | demonstrated | verified | unverified"
    )
    sophistication: Optional[str] = ""
    understanding: Optional[str] = Field(
        "", description="What the evidence shows the student actually understands."
    )
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


class TechnicalMaturitySchema(BaseModel):
    """Technical maturity classification."""

    model_config = ConfigDict(extra="ignore")

    classification: Optional[str] = Field(
        "",
        description="prototype | academic | portfolio | production_like | industry_level",
    )
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
    """
    An expected aspect the resume does not substantiate.

    This is now the *single* place an absence is recorded. Scored dimensions are
    omitted rather than filled with a "cannot be verified" sentinel, so the same
    gap is stated once instead of three times.
    """

    model_config = ConfigDict(extra="ignore")

    aspect: Optional[str] = ""
    description: Optional[str] = ""
    impact: Optional[str] = ""


class ExecutiveAssessmentSchema(BaseModel):
    """Executive-level technical summary of the project."""

    model_config = ConfigDict(extra="ignore")

    overall_impression: Optional[str] = ""
    demonstrates: List[str] = Field(default_factory=list)
    does_not_demonstrate: List[str] = Field(default_factory=list)
    strongest_signals: List[str] = Field(default_factory=list)
    weakest_signals: List[str] = Field(default_factory=list)
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)


class ProjectIntelligence(BaseModel):
    """
    Top-level validated schema for ONE project's deep intelligence report.

    This is the ``response_schema`` handed to :meth:`LLMService.analyze`. Every
    field is optional-with-default so a partially-populated model response — or a
    response salvaged after truncation — still validates and is mapped onto
    :class:`ProjectIntelligenceReport`.

    ``hiring_signal`` is a 0–100 :class:`ScoredDimensionSchema`. It is **not** a
    hiring recommendation and **not** a placement score — it measures how much
    hiring-relevant technical evidence the project provides.
    """

    model_config = ConfigDict(extra="ignore")

    understanding: UnderstandingSchema = Field(default_factory=UnderstandingSchema)
    architecture: List[ArchitectureFacetSchema] = Field(default_factory=list)
    complexity: ComplexitySchema = Field(default_factory=ComplexitySchema)
    engineering_depth: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    #: Fans out into BOTH ``technology_usage`` and ``skill_evidence`` on the report.
    skills_and_tech: List[SkillTechSchema] = Field(default_factory=list)
    competencies: List[CompetencySchema] = Field(default_factory=list)
    industry_relevance: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    technical_maturity: TechnicalMaturitySchema = Field(default_factory=TechnicalMaturitySchema)
    evidence_strength: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    hiring_signal: ScoredDimensionSchema = Field(default_factory=ScoredDimensionSchema)
    strengths: List[AssessedPointSchema] = Field(default_factory=list)
    weaknesses: List[AssessedPointSchema] = Field(default_factory=list)
    missing_evidence: List[MissingEvidenceItemSchema] = Field(default_factory=list)
    risks: List[AssessedPointSchema] = Field(default_factory=list)
    executive_assessment: ExecutiveAssessmentSchema = Field(
        default_factory=ExecutiveAssessmentSchema
    )
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)
    caveats: List[str] = Field(default_factory=list)
