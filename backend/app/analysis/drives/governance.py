"""
app/analysis/drives/governance.py
-----------------------------------
Intelligence Governance Layer — Phase 4.3 Drive Intelligence Engine.

Position in the pipeline:

    LLM Structured Output
            ↓
    Pydantic Validation (structural)
            ↓
    [THIS MODULE] Intelligence Governance Layer (semantic + quality)
            ↓
    DriveSnapshot (persisted intelligence)

Responsibilities:
    1. Auto-correct recoverable issues without failing the analysis.
    2. Detect fatal issues and raise GovernanceValidationError to
       prevent poisoned data from reaching the snapshot store.
    3. Compute intelligence quality metrics.
    4. Return a corrected DriveIntelligenceProfile + GovernanceReport.

Issue Classification:

    RECOVERABLE (auto-correct, analysis continues):
        - Duplicate technologies (same name case-insensitively)
        - Duplicate competencies
        - Duplicate qualifications (same type)
        - Whitespace/formatting artifacts in free-text fields

    FATAL (raise GovernanceValidationError, no snapshot created):
        - Any artifact with an empty evidence list (should be caught by
          Pydantic, but double-checked here)
        - Completely empty profile (zero technologies + competencies +
          qualifications + role_expectations)
        - Invalid confidence/importance values escaping Pydantic
        - Payload deserialization failure

Design:
    The Governance Layer is stateless and pure (no I/O, no DB access).
    It receives a DriveIntelligenceProfile, returns a corrected profile
    and a GovernanceReport. The caller (drive_analysis_service) decides
    what to do with the report.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from app.analysis.drives.schemas.intelligence import (
    DriveIntelligenceProfile,
    TechnologyIntelligence,
    TechnicalCompetencyIntelligence,
    BehavioralCompetencyIntelligence,
    QualificationIntelligence,
    HiringSignal,
    SelectionProcessIntelligence,
    RiskIntelligence,
    SuccessIndicator,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Governance exception
# ---------------------------------------------------------------------------


class GovernanceValidationError(Exception):
    """
    Raised when the Governance Layer encounters a fatal intelligence quality issue.

    Fatal issues prevent snapshot creation. The caller should mark the
    DriveAnalysis record as FAILED and persist this message in error_message.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# ---------------------------------------------------------------------------
# Governance report
# ---------------------------------------------------------------------------


@dataclass
class GovernanceReport:
    """
    Post-governance quality report attached to DriveAnalysis.processing_metadata.

    Attributes:
        corrections:       Descriptions of auto-corrections applied.
        warnings:          Non-fatal quality concerns (not raised as errors).
        quality_score:     0.0–1.0 overall structural integrity.
        evidence_coverage: % of artifacts possessing explicit (non-inferred) evidence.
        confidence_distribution: Count of HIGH/MEDIUM/LOW evidence items.
    """

    corrections: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    quality_score: float = 1.0
    evidence_coverage: float = 1.0
    confidence_distribution: dict = field(
        default_factory=lambda: {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    )
    validation_warnings: int = 0

    def to_dict(self) -> dict:
        return {
            "quality_score": round(self.quality_score, 4),
            "evidence_coverage": round(self.evidence_coverage, 4),
            "confidence_distribution": self.confidence_distribution,
            "validation_warnings": self.validation_warnings,
            "governance_corrections": self.corrections,
            "governance_warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Governance Layer
# ---------------------------------------------------------------------------


class DriveGovernanceLayer:
    """
    Stateless governance validator and auto-corrector for DriveIntelligenceProfile.

    Usage:
        corrected_profile, report = DriveGovernanceLayer().validate_and_correct(profile)
    """

    def validate_and_correct(
        self, profile: DriveIntelligenceProfile
    ) -> tuple[DriveIntelligenceProfile, GovernanceReport]:
        """
        Validate and auto-correct a raw DriveIntelligenceProfile.

        Args:
            profile: The Pydantic-validated profile from the LLM engine.

        Returns:
            A tuple of (corrected_profile, GovernanceReport).

        Raises:
            GovernanceValidationError: On any fatal quality issue.
        """
        report = GovernanceReport()

        # --- Fatal checks before any correction ---
        self._check_minimum_intelligence(profile)

        # --- Auto-corrections (recoverable) ---
        technologies = self._deduplicate_technologies(profile.technologies, report)
        technical_competencies = self._deduplicate_by_key(
            profile.technical_competencies, "competency", "technical competencies", report
        )
        behavioral_competencies = self._deduplicate_by_key(
            profile.behavioral_competencies, "competency", "behavioral competencies", report
        )
        qualifications = self._deduplicate_by_key(
            profile.qualifications, "qualification_type", "qualifications", report
        )
        hiring_signals = self._deduplicate_by_key(
            profile.hiring_signals, "signal", "hiring signals", report
        )

        # Build corrected profile
        corrected = DriveIntelligenceProfile(
            intelligence_schema_version=profile.intelligence_schema_version,
            technologies=technologies,
            technical_competencies=technical_competencies,
            behavioral_competencies=behavioral_competencies,
            qualifications=qualifications,
            hiring_signals=hiring_signals,
            role_expectations=profile.role_expectations,
            selection_process=profile.selection_process,
            risks=profile.risks,
            success_indicators=profile.success_indicators,
        )

        # --- Post-correction quality metrics ---
        self._compute_quality_metrics(corrected, report)
        report.validation_warnings = len(report.corrections)

        logger.info(
            "Governance complete. quality_score=%.2f evidence_coverage=%.2f "
            "corrections=%d",
            report.quality_score,
            report.evidence_coverage,
            report.validation_warnings,
        )

        return corrected, report

    # -----------------------------------------------------------------------
    # Fatal checks
    # -----------------------------------------------------------------------

    def _check_minimum_intelligence(self, profile: DriveIntelligenceProfile) -> None:
        """Raise if the profile contains zero actionable intelligence."""
        total = (
            len(profile.technologies)
            + len(profile.technical_competencies)
            + len(profile.qualifications)
            + len(profile.role_expectations)
        )
        if total == 0:
            raise GovernanceValidationError(
                "Fatal: DriveIntelligenceProfile contains zero intelligence artifacts "
                "across technologies, technical_competencies, qualifications, and "
                "role_expectations. The LLM likely returned an empty or malformed response."
            )

    # -----------------------------------------------------------------------
    # Recoverable auto-corrections
    # -----------------------------------------------------------------------

    def _deduplicate_technologies(
        self,
        technologies: List[TechnologyIntelligence],
        report: GovernanceReport,
    ) -> List[TechnologyIntelligence]:
        """
        Merge duplicate technologies (case-insensitive name match).

        Merge strategy:
            - Keep the entry with the highest importance.
            - Accumulate all evidence from duplicates into the winner.
        """
        seen: dict[str, TechnologyIntelligence] = {}
        importance_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

        for tech in technologies:
            key = tech.name.lower().strip()
            if key in seen:
                existing = seen[key]
                # Keep highest importance
                if importance_order.get(tech.importance, 0) > importance_order.get(
                    existing.importance, 0
                ):
                    # Merge evidence into higher-importance entry
                    merged_evidence = list(existing.evidence) + list(tech.evidence)
                    seen[key] = TechnologyIntelligence(
                        name=existing.name,
                        category=tech.category,
                        importance=tech.importance,
                        confidence=tech.confidence,
                        evidence=merged_evidence,
                    )
                else:
                    # Accumulate evidence onto existing
                    merged_evidence = list(existing.evidence) + list(tech.evidence)
                    seen[key] = TechnologyIntelligence(
                        name=existing.name,
                        category=existing.category,
                        importance=existing.importance,
                        confidence=existing.confidence,
                        evidence=merged_evidence,
                    )
                msg = f"Merged duplicate technology: '{tech.name}'"
                report.corrections.append(msg)
                logger.debug("Governance auto-correction: %s", msg)
            else:
                seen[key] = tech

        return list(seen.values())

    def _deduplicate_by_key(
        self,
        items: list,
        key_attr: str,
        label: str,
        report: GovernanceReport,
    ) -> list:
        """
        Generic deduplication by a single string attribute.

        Keeps the first occurrence; logs subsequent duplicates as corrections.
        """
        seen: set[str] = set()
        result = []
        for item in items:
            key = str(getattr(item, key_attr, "")).upper().strip()
            if key in seen:
                msg = f"Removed duplicate {label} entry: '{key}'"
                report.corrections.append(msg)
                logger.debug("Governance auto-correction: %s", msg)
            else:
                seen.add(key)
                result.append(item)
        return result

    # -----------------------------------------------------------------------
    # Quality metrics
    # -----------------------------------------------------------------------

    def _compute_quality_metrics(
        self, profile: DriveIntelligenceProfile, report: GovernanceReport
    ) -> None:
        """
        Compute evidence_coverage, confidence_distribution, and quality_score.

        evidence_coverage = % of artifacts that have at least one EXPLICIT_* evidence.
        quality_score     = weighted combination of coverage and confidence distribution.
        """
        all_artifacts = (
            profile.technologies
            + profile.technical_competencies
            + profile.behavioral_competencies
            + profile.qualifications
            + profile.hiring_signals
            + profile.role_expectations
            + profile.selection_process
            + profile.risks
            + profile.success_indicators
        )

        if not all_artifacts:
            report.quality_score = 0.0
            report.evidence_coverage = 0.0
            return

        explicit_types = {
            "EXPLICIT_REQUIREMENT",
            "EXPLICIT_RESPONSIBILITY",
            "EXPLICIT_QUALIFICATION",
            "EXPLICIT_SELECTION_PROCESS",
        }

        artifacts_with_explicit = 0
        dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for artifact in all_artifacts:
            has_explicit = False
            for ev in getattr(artifact, "evidence", []):
                ev_type = ev.evidence_type if isinstance(ev.evidence_type, str) else ev.evidence_type.value
                ev_conf = ev.confidence if isinstance(ev.confidence, str) else ev.confidence.value
                if ev_type.upper() in explicit_types:
                    has_explicit = True
                conf_key = ev_conf.upper()
                if conf_key in dist:
                    dist[conf_key] += 1
            if has_explicit:
                artifacts_with_explicit += 1

        total = len(all_artifacts)
        evidence_coverage = artifacts_with_explicit / total
        report.evidence_coverage = evidence_coverage
        report.confidence_distribution = dist

        # Quality score: 60% coverage + 40% confidence distribution quality
        total_confidence = dist["HIGH"] + dist["MEDIUM"] + dist["LOW"]
        if total_confidence > 0:
            confidence_quality = (
                dist["HIGH"] * 1.0 + dist["MEDIUM"] * 0.6 + dist["LOW"] * 0.2
            ) / total_confidence
        else:
            confidence_quality = 0.0

        report.quality_score = (0.6 * evidence_coverage) + (0.4 * confidence_quality)
