"""
app/analysis/drives/governance.py
-----------------------------------
Intelligence Governance Layer — Phase 4.3 & 4.5 Drive Intelligence Engine.

Position in the pipeline:

    LLM Structured Output
            ↓
    Pydantic Validation (structural)
            ↓
    [THIS MODULE] Intelligence Governance Layer (semantic + quality + sanitization)
            ↓
    DriveSnapshot (persisted intelligence)

Responsibilities:
    1. Auto-correct recoverable issues without failing the analysis.
    2. Normalize & sanitize subdomains, role_family, and technology names.
    3. Detect fatal issues and raise GovernanceValidationError to
       prevent poisoned data from reaching the snapshot store.
    4. Compute intelligence quality metrics across all 15+ artifact categories.
    5. Return a corrected DriveIntelligenceProfile + GovernanceReport.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.drives.schemas.intelligence import (
    DriveDifficultyIntelligence,
    DriveIntelligenceProfile,
    PlacementRelevanceIntelligence,
    PreparationIntelligence,
    PreparationTopic,
    ProfessionalDomainIntelligence,
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
    """

    def validate_and_correct(
        self, profile: DriveIntelligenceProfile
    ) -> tuple[DriveIntelligenceProfile, GovernanceReport]:
        """
        Validate, sanitize, and auto-correct a raw DriveIntelligenceProfile.

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
        domain = self._sanitize_domain(profile.domain, report)
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
        preparation = self._sanitize_preparation(profile.preparation, report)

        # Build corrected profile preserving all 15+ artifact categories
        corrected = DriveIntelligenceProfile(
            intelligence_schema_version=profile.intelligence_schema_version,
            domain=domain,
            technologies=technologies,
            technical_competencies=technical_competencies,
            behavioral_competencies=behavioral_competencies,
            qualifications=qualifications,
            hiring_signals=hiring_signals,
            role_expectations=profile.role_expectations,
            selection_process=profile.selection_process,
            risks=profile.risks,
            success_indicators=profile.success_indicators,
            service_agreements=profile.service_agreements,
            work_arrangements=profile.work_arrangements,
            shifts=profile.shifts,
            experience_requirements=profile.experience_requirements,
            compensation=profile.compensation,
            preparation=preparation,
            # Phase 4.4 — Evaluation Engine artifacts (passed through as-is; no auto-correction)
            difficulty=profile.difficulty,
            placement_relevance=profile.placement_relevance,
        )

        # --- Post-correction quality metrics ---
        self._compute_quality_metrics(corrected, report)
        report.validation_warnings = len(report.corrections)

        logger.info(
            "Governance complete. quality_score=%.2f evidence_coverage=%.2f corrections=%d",
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
    # Recoverable auto-corrections & sanitization
    # -----------------------------------------------------------------------

    def _sanitize_domain(
        self,
        domain: Optional[ProfessionalDomainIntelligence],
        report: GovernanceReport,
    ) -> Optional[ProfessionalDomainIntelligence]:
        """
        Sanitize and normalize subdomains and role family.
        """
        if not domain:
            return None

        sanitized_subdomains: List[str] = []
        seen = set()
        for sub in domain.subdomains:
            cleaned = sub.strip().title()
            if cleaned and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                sanitized_subdomains.append(cleaned)

        # Limit to max 5 subdomains
        if len(sanitized_subdomains) > 5:
            sanitized_subdomains = sanitized_subdomains[:5]
            report.corrections.append("Trimmed subdomains to top 5.")

        role_fam = domain.role_family.strip().title() if domain.role_family else None

        return ProfessionalDomainIntelligence(
            domain=domain.domain,
            subdomains=sanitized_subdomains,
            role_family=role_fam,
            industry=domain.industry,
            confidence=domain.confidence,
            evidence=domain.evidence,
        )

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
                tech_imp = tech.importance if isinstance(tech.importance, str) else tech.importance.value
                exist_imp = existing.importance if isinstance(existing.importance, str) else existing.importance.value
                # Keep highest importance
                if importance_order.get(tech_imp.upper(), 0) > importance_order.get(
                    exist_imp.upper(), 0
                ):
                    merged_evidence = list(existing.evidence) + list(tech.evidence)
                    seen[key] = TechnologyIntelligence(
                        name=existing.name,
                        category=tech.category,
                        importance=tech.importance,
                        confidence=tech.confidence,
                        is_mandatory=tech.is_mandatory if tech.is_mandatory is not None else existing.is_mandatory,
                        origin=tech.origin,
                        evidence=merged_evidence,
                    )
                else:
                    merged_evidence = list(existing.evidence) + list(tech.evidence)
                    seen[key] = TechnologyIntelligence(
                        name=existing.name,
                        category=existing.category,
                        importance=existing.importance,
                        confidence=existing.confidence,
                        is_mandatory=existing.is_mandatory if existing.is_mandatory is not None else tech.is_mandatory,
                        origin=existing.origin,
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

    def _sanitize_preparation(
        self,
        preparation: Optional[PreparationIntelligence],
        report: GovernanceReport,
    ) -> Optional[PreparationIntelligence]:
        """
        Deduplicate priority preparation topics by (topic_name, target_round_type).
        """
        if not preparation:
            return None

        seen_topics: set[tuple[str, str]] = set()
        deduped_topics: List[PreparationTopic] = []

        for topic in preparation.priority_topics:
            round_str = str(topic.target_round_type.value if hasattr(topic.target_round_type, 'value') else topic.target_round_type)
            key = (topic.topic_name.lower().strip(), round_str)
            if key not in seen_topics:
                seen_topics.add(key)
                deduped_topics.append(topic)
            else:
                msg = f"Removed duplicate preparation topic: '{topic.topic_name}' for round '{round_str}'"
                report.corrections.append(msg)

        return PreparationIntelligence(
            priority_topics=deduped_topics,
            key_evaluation_focus=preparation.key_evaluation_focus,
        )

    # -----------------------------------------------------------------------
    # Quality metrics
    # -----------------------------------------------------------------------

    def _compute_quality_metrics(
        self, profile: DriveIntelligenceProfile, report: GovernanceReport
    ) -> None:
        """
        Compute evidence_coverage, confidence_distribution, and quality_score.
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
            + profile.service_agreements
            + profile.work_arrangements
            + profile.shifts
            + profile.experience_requirements
            + profile.compensation
        )
        if profile.domain:
            all_artifacts.append(profile.domain)
        if profile.preparation:
            all_artifacts.extend(profile.preparation.priority_topics)
        # Phase 4.4 — Include evaluation intelligence artifacts in quality metrics
        if profile.difficulty:
            all_artifacts.append(profile.difficulty)
        if profile.placement_relevance:
            all_artifacts.append(profile.placement_relevance)

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
                if str(ev_type).upper() in explicit_types:
                    has_explicit = True
                conf_key = str(ev_conf).upper()
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
