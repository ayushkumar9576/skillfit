"""
app/analysis/engines/drive_intelligence_engine.py
---------------------------------------------------
Drive Intelligence Engine — Phase 4.3.

Responsibility:
    Transform a ParsedDriveContent into a validated, governance-approved
    DriveIntelligenceProfile by orchestrating LLM structured extraction.

Source Boundary Rule (enforced here):
    This engine ONLY accepts ParsedDriveContent as input. It never reads:
        - Raw PDF files
        - Uploaded file bytes
        - DriveSource directly

    The only valid call path is:
        DriveSource
              ↓
        ParsedDriveContent (from drive_ingestion_service.get_parsed_content)
              ↓
        DriveIntelligenceEngine.analyze()

Pipeline:
    1. Retrieve versioned prompt from the prompt registry.
    2. Format the user message with drive metadata + normalized content.
    3. Call LLMService.analyze() with DriveIntelligenceProfile as response_schema.
    4. Pass the Pydantic-validated profile through the Governance Layer.
    5. Return the corrected profile + governance report + provenance metadata.

Versioning:
    ANALYSIS_VERSION   — code version of this engine.
    prompt_version     — which prompt template was used (from prompts.py registry).
    model_name         — the exact LLM model that produced the output.

All three are recorded in DriveAnalysis for full auditability.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from app.analysis.drives.governance import (
    DriveGovernanceLayer,
    GovernanceReport,
    GovernanceValidationError,
)
from app.analysis.drives.evidence_validator import verify_evidence
from app.analysis.drives.consistency_validator import verify_consistency
from app.analysis.drives.schemas.intelligence import DriveIntelligenceProfile
from app.analysis.drives.schemas.prompts import DEFAULT_PROMPT_VERSION, get_prompt
from app.drives.parsers.contract import ParsedDriveContent
from app.services.llm.exceptions import LLMError
from app.services.llm.service import LLMService, get_llm_service

logger = logging.getLogger(__name__)

# Current engine version — bump on any logic change to this file
ANALYSIS_VERSION: str = "4.3.0"

_DEFAULT_MAX_TOKENS = 8192
_DEFAULT_TEMPERATURE = 0.0


# ---------------------------------------------------------------------------
# Engine result container
# ---------------------------------------------------------------------------


@dataclass
class DriveIntelligenceResult:
    """
    Container wrapping all outputs of a single DriveIntelligenceEngine.analyze() call.

    Attributes:
        profile:           The corrected, governance-approved DriveIntelligenceProfile.
        governance_report: Post-governance quality metrics and correction log.
        prompt_version:    The prompt template version that was used.
        model_name:        The exact LLM model that produced the output.
        analysis_version:  The engine code version.
        raw_llm_output:    The raw JSON string returned by the LLM (for debugging).
        token_usage:       Provider-reported token counts.
    """

    profile: DriveIntelligenceProfile
    governance_report: GovernanceReport
    prompt_version: str
    model_name: str
    analysis_version: str
    raw_llm_output: str
    token_usage: dict


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class DriveIntelligenceEngine:
    """
    Orchestrates Drive Intelligence extraction from ParsedDriveContent.

    Dependency injection allows the LLM service to be replaced with a mock
    in tests — no real API key required for unit testing.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = _DEFAULT_TEMPERATURE,
        prompt_version: str = DEFAULT_PROMPT_VERSION,
    ) -> None:
        self._llm_service = llm_service
        self._model = model
        self._max_tokens = max_tokens or int(
            os.getenv("LLM_MAX_TOKENS", str(_DEFAULT_MAX_TOKENS))
        )
        self._temperature = temperature
        self._prompt_version = prompt_version
        self._governance = DriveGovernanceLayer()

    async def analyze(
        self,
        *,
        content: ParsedDriveContent,
        company_name: str = "",
        role: str = "",
    ) -> DriveIntelligenceResult:
        """
        Extract Drive Intelligence from normalized JD content.

        SOURCE BOUNDARY: Only accepts ParsedDriveContent — never raw files.

        Args:
            content:      The normalized drive content from the ingestion pipeline.
            company_name: Drive company name (injected into prompt for context).
            role:         Drive role/title (injected into prompt for context).

        Returns:
            DriveIntelligenceResult with the corrected profile and governance report.

        Raises:
            GovernanceValidationError: If the LLM output fails governance checks.
            LLMError: If the LLM provider fails after retries.
        """
        # Derive character count from statistics dict (actual contract shape)
        char_count = content.statistics.get("character_count", 0) if isinstance(
            getattr(content, "statistics", None), dict
        ) else getattr(content, "character_count", 0)

        logger.info(
            "DriveIntelligenceEngine.analyze() start | company=%r role=%r "
            "content_chars=%d prompt_version=%s",
            company_name,
            role,
            char_count,
            self._prompt_version,
        )

        # Step 1: Resolve versioned prompt
        system_prompt, user_template = get_prompt(self._prompt_version)
        # Resolve normalized content from the contract's field name
        normalized_content = (
            getattr(content, "normalized_text", None)
            or getattr(content, "normalized_content", "")
        )
        user_content = user_template.format(
            company_name=company_name or "Unknown Company",
            role=role or "Unknown Role",
            normalized_content=normalized_content,
        )

        # Step 2: Resolve LLM service
        llm_service = self._llm_service or get_llm_service()

        # Step 3: LLM call with DriveIntelligenceProfile as structured schema
        try:
            completion = await llm_service._provider.complete_structured(
                system_prompt=system_prompt,
                user_content=user_content,
                response_schema=DriveIntelligenceProfile,
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
        except LLMError as exc:
            logger.error(
                "DriveIntelligenceEngine: LLM failed | error=%s",
                exc,
                exc_info=True,
            )
            raise

        raw_profile: DriveIntelligenceProfile = completion.parsed
        raw_llm_output: str = completion.raw_text
        model_name: str = completion.model
        token_usage = {
            "input_tokens": completion.usage.prompt_tokens,
            "output_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens,
        }

        logger.info(
            "LLM extraction complete | model=%s tokens_total=%d",
            model_name,
            token_usage["total_tokens"],
        )

        # Step 4: Governance Layer (validation + auto-correction + quality metrics)
        try:
            # First, semantic and evidence validation
            verify_consistency(raw_profile)
            verify_evidence(raw_profile, normalized_content)
            
            # Then standard auto-correction and metric generation
            corrected_profile, governance_report = self._governance.validate_and_correct(
                raw_profile
            )
        except GovernanceValidationError:
            logger.error(
                "DriveIntelligenceEngine: Governance validation FAILED | "
                "technologies=%d competencies=%d qualifications=%d",
                len(raw_profile.technologies),
                len(raw_profile.technical_competencies),
                len(raw_profile.qualifications),
            )
            raise

        logger.info(
            "DriveIntelligenceEngine.analyze() complete | "
            "quality_score=%.2f evidence_coverage=%.2f corrections=%d",
            governance_report.quality_score,
            governance_report.evidence_coverage,
            governance_report.validation_warnings,
        )

        return DriveIntelligenceResult(
            profile=corrected_profile,
            governance_report=governance_report,
            prompt_version=self._prompt_version,
            model_name=model_name,
            analysis_version=ANALYSIS_VERSION,
            raw_llm_output=raw_llm_output,
            token_usage=token_usage,
        )
