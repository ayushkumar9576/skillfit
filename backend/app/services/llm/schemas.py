"""
app/services/llm/schemas.py
---------------------------
Reusable Pydantic v2 primitives for the SkillFit LLM Integration Layer
(Phase 3.6) and a strict JSON-response validation helper.

These are the *structured-output* building blocks that future analyzers
(Phase 3.7+) compose into their own response schemas. They are deliberately
generic — no project/internship/skill-specific fields live here.

Conventions (mirrors app/schemas/resume.py):
    - Pydantic v2 (`ConfigDict`, `Field(..., description=...)`).
    - `extra="ignore"` so a slightly chatty model response (extra keys) is
      tolerated rather than rejected — we only enforce the fields we require.
    - Reuses the shared `ConfidenceLevel` enum from app.core.enums.
"""

import json
import logging
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.enums import ConfidenceLevel
from app.services.llm.exceptions import LLMResponseError

logger = logging.getLogger(__name__)

# TypeVar so validate_response() preserves the concrete schema type for callers.
TSchema = TypeVar("TSchema", bound=BaseModel)


class Evidence(BaseModel):
    """
    A single piece of resume-derived evidence supporting a finding.

    Mirrors the intent of the pure-dataclass ``AnalysisEvidence`` used elsewhere
    in the analysis domain, but as a Pydantic model so it can be validated
    directly out of LLM JSON output.
    """

    model_config = ConfigDict(extra="ignore")

    text: str = Field(
        ...,
        description="Verbatim or normalized statement from the resume that supports the finding.",
    )
    source_section: Optional[str] = Field(
        None,
        description="Canonical resume section the evidence came from (e.g. 'projects', 'skills').",
    )
    confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence (0.0–1.0) that this evidence genuinely supports the finding.",
    )


class Finding(BaseModel):
    """
    A single analytical conclusion the model drew from the evidence.

    Evidence-based philosophy: every finding should be backed by concrete
    ``evidence`` drawn from the resume, not asserted in a vacuum.
    """

    model_config = ConfigDict(extra="ignore")

    statement: str = Field(
        ...,
        description="The conclusion or claim being made about the candidate.",
    )
    reasoning: Optional[str] = Field(
        None,
        description="Short justification linking the evidence to the statement.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence (0.0–1.0) in this finding.",
    )
    confidence_level: Optional[ConfidenceLevel] = Field(
        None,
        description="Optional coarse confidence band ('low' | 'medium' | 'high').",
    )
    evidence: List[Evidence] = Field(
        default_factory=list,
        description="Resume-derived evidence supporting this finding.",
    )


class StructuredAnalysis(BaseModel):
    """
    Generic base container for an analyzer's structured output.

    Future analyzers may either use this directly or subclass/compose it with
    their own domain fields. Provided so the infrastructure has a concrete,
    testable default schema before any analyzer exists.
    """

    model_config = ConfigDict(extra="ignore")

    summary: Optional[str] = Field(
        None,
        description="Brief natural-language summary of the analysis.",
    )
    findings: List[Finding] = Field(
        default_factory=list,
        description="Individual evidence-backed findings.",
    )


class LLMUsage(BaseModel):
    """
    Normalized token-usage + provenance for a single completion.

    Carries ``provider`` and ``model`` so every result traces back to the exact
    provider/model that produced it (used by the usage tracker and returned on
    every ``LLMCompletion``).
    """

    model_config = ConfigDict(extra="ignore")

    provider: str = Field(..., description="Provider that produced the completion (e.g. 'openai').")
    model: str = Field(..., description="Concrete model that produced the completion.")
    prompt_tokens: int = Field(0, ge=0, description="Tokens consumed by the prompt.")
    completion_tokens: int = Field(0, ge=0, description="Tokens generated in the completion.")
    total_tokens: int = Field(0, ge=0, description="Total tokens (prompt + completion).")


def _repair_truncated_json(raw_text: str) -> Optional[str]:
    """
    Rebuild parseable JSON from a response that was cut off mid-generation.

    A response truncated at the output-token cap is *valid JSON up to the cut* —
    only the closing brackets (and possibly one half-written value) are missing.
    Because analyzer schemas are optional-with-default throughout, recovering the
    complete prefix yields a partial-but-useful report, which is far better than
    discarding the whole analysis over the last few characters.

    Strategy — one pass, tracking string/escape state and the open-container
    stack, remembering the last offset at which the document was safely
    closable:

        - a string that closes and is NOT followed by ``:`` is a finished value;
        - ``}`` / ``]`` finishes a container;
        - ``,`` means everything before it is finished (so the cut goes *before*
          the comma, discarding whatever partial element followed).

    The text is then truncated to that offset and the recorded stack is closed.
    A half-written key, number, or string after the last safe point is dropped;
    the schema default fills its place.

    Args:
        raw_text: The (possibly truncated) raw model response.

    Returns:
        A repaired JSON string, or ``None`` when nothing salvageable was found
        (e.g. the response was never JSON in the first place).
    """
    stack: List[str] = []
    in_string = False
    escaped = False
    safe_end = -1
    safe_stack: List[str] = []
    length = len(raw_text)

    index = 0
    while index < length:
        char = raw_text[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
                # Distinguish a finished value from an object key: a key is
                # followed by ':', and cutting there would strand it. If the
                # quote is the last thing in the document we cannot tell which
                # it was, so treat it as unsafe and fall back to the previous
                # safe point — dropping one field beats emitting invalid JSON.
                probe = index + 1
                while probe < length and raw_text[probe] in " \t\r\n":
                    probe += 1
                if probe < length and raw_text[probe] != ":":
                    safe_end, safe_stack = index + 1, list(stack)
            index += 1
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in "}]":
            if stack:
                stack.pop()
            safe_end, safe_stack = index + 1, list(stack)
        elif char == ",":
            safe_end, safe_stack = index, list(stack)

        index += 1

    if safe_end <= 0:
        return None

    repaired = raw_text[:safe_end] + "".join(reversed(safe_stack))
    # An unclosed outermost object means the response never even opened one.
    return repaired if repaired.lstrip().startswith(("{", "[")) else None


def validate_response(raw_text: Optional[str], schema: Type[TSchema]) -> TSchema:
    """
    Parse ``raw_text`` as JSON and validate it against ``schema``.

    This is the single enforcement point that turns a raw model string into a
    typed, validated Pydantic object — the contract every analyzer relies on.

    When the text is not parseable, one salvage attempt is made via
    :func:`_repair_truncated_json` before giving up, so a response cut off at the
    token cap degrades to a partial report rather than a lost one. Salvage is
    logged at WARNING because it means the output budget was exceeded.

    Args:
        raw_text: The raw response content returned by the provider.
        schema:   The Pydantic model the response must conform to.

    Returns:
        A validated instance of ``schema``.

    Raises:
        LLMResponseError: if the text is missing, is not valid JSON (and cannot
            be salvaged), or fails schema validation. The message is sanitized —
            it reports *that* validation failed and a field-level summary, but
            never echoes the full raw model output.
    """
    if raw_text is None or raw_text.strip() == "":
        raise LLMResponseError("Model returned an empty response.")

    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError) as exc:
        repaired = _repair_truncated_json(raw_text)
        if repaired is None:
            raise LLMResponseError("Model response was not valid JSON.") from exc
        try:
            data = json.loads(repaired)
        except (json.JSONDecodeError, TypeError):
            raise LLMResponseError("Model response was not valid JSON.") from exc
        logger.warning(
            "Model response appears truncated; salvaged %d of %d characters as a "
            "partial %s. Consider raising the output-token budget.",
            len(repaired), len(raw_text), schema.__name__,
        )

    try:
        def _normalize_llm_json(obj) -> None:
            """Recursively normalize known hallucinated values in the JSON payload."""
            if isinstance(obj, dict):
                # 1. Normalize 'importance' mapping
                if "importance" in obj and isinstance(obj["importance"], str):
                    mapping = {
                        "PREFERRED": "MEDIUM",
                        "OPTIONAL": "LOW",
                        "REQUIRED": "HIGH",
                        "MANDATORY": "CRITICAL"
                    }
                    val = obj["importance"].upper()
                    if val in mapping:
                        obj["importance"] = mapping[val]
                
                # Recursively normalize nested objects/lists
                for value in obj.values():
                    _normalize_llm_json(value)
            elif isinstance(obj, list):
                for item in obj:
                    _normalize_llm_json(item)

        _normalize_llm_json(data)
        
        if schema.__name__ == "DriveIntelligenceProfile":
            print("================================================================================")
            print("RAW DRIVE INTELLIGENCE RESPONSE")
            print("===============================")
            print(json.dumps(data, indent=2, default=str))

        return schema.model_validate(data)
    except ValidationError as exc:
        if schema.__name__ == "DriveIntelligenceProfile":
            print("================================================================================")
            print("DRIVE PROFILE VALIDATION FAILED")
            print("===============================")
            for err in exc.errors():
                print(f"Field: {'.'.join(str(loc) for loc in err['loc'])}")
                print(f"Error: {err['msg']}")
                print(f"Input: {err.get('input', 'N/A')}\n")
            print("Errors JSON:")
            print(exc.json())
            
        raise LLMResponseError(
            f"Model response failed {schema.__name__} validation "
            f"({exc.error_count()} error(s))."
        ) from exc
