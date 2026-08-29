"""
app/analysis/engines/certification_schemas.py
---------------------------------------------
Pydantic v2 LLM boundary schemas for the SkillFit Certification Analysis Engine
(Phase 3 Remediation).

Architecture Principle:
    LLM = Structured Qualitative Intelligence
    Python = All Scores, Tiers, Confidence, Rankings

The LLM evaluates:
    - What category of certification this is
    - Which competencies it supports
    - Which domains it maps to
    - Industry recognition level (qualitative)
    - Practical strength (theory-heavy vs. implementation-supporting)
    - Explicit limitations

The LLM does NOT generate:
    - Numerical scores
    - Confidence percentages
    - Hiring scores
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Certification Intelligence Schema
# ---------------------------------------------------------------------------

class CertificationIntelligenceSchema(BaseModel):
    """
    Structured intelligence for ONE certification.

    supported_competencies must use values from the canonical CompetencyType taxonomy.
    supported_domains must use values from the canonical DomainType taxonomy.
    industry_recognition must be one of: "high" | "moderate" | "low" | "unknown"
    practical_strength must be one of: "implementation-supporting" | "theory-heavy" | "mixed"
    """
    model_config = ConfigDict(extra="ignore")

    certification_name: Optional[str] = ""
    category: Optional[str] = Field(
        "",
        description="High-level category: Cloud | Data Science | Security | Software Engineering | etc."
    )
    supported_competencies: List[str] = Field(
        default_factory=list,
        description="CompetencyType values this certification validates."
    )
    supported_domains: List[str] = Field(
        default_factory=list,
        description="DomainType values this certification signals."
    )
    industry_recognition: Optional[str] = Field(
        "unknown",
        description="high | moderate | low | unknown"
    )
    practical_strength: Optional[str] = Field(
        "theory-heavy",
        description="implementation-supporting | theory-heavy | mixed"
    )
    limitations: List[str] = Field(
        default_factory=list,
        description="Explicit capability gaps this cert does NOT validate."
    )


# ---------------------------------------------------------------------------
# Batch schema for analyzing multiple certifications in one LLM call
# ---------------------------------------------------------------------------

class CertificationBatchIntelligence(BaseModel):
    """
    Batch output for analyzing multiple certifications in a single LLM call.
    Expects one CertificationIntelligenceSchema entry per input certification.
    """
    model_config = ConfigDict(extra="ignore")

    certifications: List[CertificationIntelligenceSchema] = Field(default_factory=list)
