"""
app/analysis/drives/consistency_validator.py
--------------------------------------------
Governance layer semantic consistency validator for Drive Intelligence.

Ensures that the LLM has not extracted logically contradictory intelligence,
such as a technology being both required and optional, or conflicting
eligibility criteria.

Phase 4.4 — Extended with evaluation intelligence consistency checks:
    - DriveDifficultyIntelligence level must be coherent with difficulty factors.
    - PlacementRelevanceIntelligence must align with signals present in the profile.
"""
import logging
from collections import defaultdict
from typing import Set

from app.analysis.drives.governance import GovernanceValidationError
from app.analysis.drives.schemas.intelligence import DriveIntelligenceProfile
from app.core.enums import (
    DriveDifficultyLevel,
    ExperienceLevel,
    HiringSignalType,
    QualificationOperator,
    QualificationType,
    TechnicalCompetencyType,
)

logger = logging.getLogger(__name__)


def verify_consistency(profile: DriveIntelligenceProfile) -> None:
    """
    Verify that the extracted profile contains no semantic contradictions.

    Args:
        profile: The extracted DriveIntelligenceProfile.

    Raises:
        GovernanceValidationError: If any logical contradictions are detected.
    """
    _check_technology_contradictions(profile)
    _check_qualification_contradictions(profile)
    _check_experience_contradictions(profile)
    # Phase 4.4 — Evaluation intelligence consistency
    if profile.difficulty is not None:
        _check_difficulty_consistency(profile)
    if profile.placement_relevance is not None:
        _check_relevance_consistency(profile)


def _check_technology_contradictions(profile: DriveIntelligenceProfile) -> None:
    """
    Detect if the same technology is listed as both mandatory and optional.
    """
    tech_map = defaultdict(set)
    for tech in profile.technologies:
        normalized_name = tech.name.strip().lower()
        if tech.is_mandatory is not None:
            tech_map[normalized_name].add(tech.is_mandatory)

    for name, mandatory_flags in tech_map.items():
        if True in mandatory_flags and False in mandatory_flags:
            logger.error("Technology contradiction detected: %r is both required and optional.", name)
            raise GovernanceValidationError(
                f"Contradictory intelligence: Technology '{name}' is marked as both mandatory and preferred."
            )


def _check_qualification_contradictions(profile: DriveIntelligenceProfile) -> None:
    """
    Detect conflicting eligibility rules.
    """
    branches_in = set()
    branches_not_in = set()

    for qual in profile.qualifications:
        if qual.qualification_type == QualificationType.branch:
            if qual.operator == QualificationOperator.in_op and qual.allowed_values:
                branches_in.update(qual.allowed_values)
            elif qual.operator == QualificationOperator.not_in and qual.allowed_values:
                branches_not_in.update(qual.allowed_values)

    if branches_in and branches_not_in:
        overlap = branches_in.intersection(branches_not_in)
        if overlap:
            logger.error("Branch contradiction detected: overlap in allowed and restricted branches %r", overlap)
            raise GovernanceValidationError(
                f"Contradictory intelligence: Conflicting branch requirements detected for: {overlap}"
            )


def _check_experience_contradictions(profile: DriveIntelligenceProfile) -> None:
    """
    Detect if the drive requires both FRESHER and LATERAL experience levels simultaneously.
    """
    levels = {exp.level for exp in profile.experience_requirements}
    if ExperienceLevel.fresher in levels and ExperienceLevel.lateral in levels:
        logger.error("Experience contradiction detected: both FRESHER and LATERAL extracted.")
        raise GovernanceValidationError(
            "Contradictory intelligence: Drive cannot require both FRESHER and LATERAL experience."
        )


# ---------------------------------------------------------------------------
# Phase 4.4 — Evaluation Intelligence Consistency Validators
# ---------------------------------------------------------------------------

# Difficulty factors that signal HIGH competitive pressure.
# Any 2+ of these together rule out BEGINNER and MODERATE.
_HIGH_SELECTIVITY_FACTORS: frozenset[str] = frozenset({
    "strong dsa focus",
    "multiple elimination rounds",
    "tier-1 company",
    "advanced technology expectations",
    "exceptional compensation",
    "high applicant volume",
    "strong project expectations",
    "prior internship preference",
    "strict cgpa requirement",
    "advanced algorithm requirements",
})

# Elite-level factors — any single one of these rules out BEGINNER.
_ELITE_INDICATOR_FACTORS: frozenset[str] = frozenset({
    "tier-1 company",
    "multiple elimination rounds",
    "strong dsa focus",
})

# DSA / ML / technical competency checks.
_ML_COMPETENCIES: frozenset = frozenset({
    TechnicalCompetencyType.machine_learning,
    TechnicalCompetencyType.machine_learning.value,
})

_ML_SIGNALS: frozenset = frozenset({
    HiringSignalType.research_focused,
    HiringSignalType.research_focused.value,
})

_ML_PROFILE_KEYWORDS: frozenset[str] = frozenset({
    "deep learning",
    "machine learning",
    "ai",
    "ml",
    "data scientist",
    "research",
    "neural network",
    "computer vision",
    "nlp",
})


def _check_difficulty_consistency(profile: DriveIntelligenceProfile) -> None:
    """
    Reject obviously inconsistent difficulty classifications.

    Deterministic mapping guide:
        ELITE requires:        Tier-1 Company + Strong DSA Focus + Multiple Elimination Rounds
        HIGHLY_COMPETITIVE:    Strong DSA Focus + 2+ high-selectivity factors
        COMPETITIVE:           Multiple high-selectivity factors present
        MODERATE:              Few or no high-selectivity factors
        BEGINNER:              No high-selectivity factors at all

    This validator enforces the lower bound only — e.g., BEGINNER is rejected
    when elite signals are present. The upper bound (e.g. "must be ELITE") is
    not enforced because the LLM may legitimately classify a partial ELITE as
    HIGHLY_COMPETITIVE.
    """
    difficulty = profile.difficulty
    if difficulty is None:
        return

    level_str = difficulty.level if isinstance(difficulty.level, str) else difficulty.level.value
    level = level_str.upper()

    # Normalize factors for comparison
    normalized_factors: Set[str] = {
        f.strip().lower() for f in difficulty.difficulty_factors
    }

    # Count how many elite/high-selectivity signals are present
    elite_hits = sum(1 for f in _ELITE_INDICATOR_FACTORS if f in normalized_factors)
    high_hits = sum(1 for f in _HIGH_SELECTIVITY_FACTORS if f in normalized_factors)

    # Also count signals from the broader intelligence profile
    has_dsa_signal = any(
        (s.signal == HiringSignalType.dsa_focused or s.signal == HiringSignalType.dsa_focused.value)
        for s in profile.hiring_signals
    )
    has_multi_rounds = len(profile.selection_process) >= 3
    has_strict_eligibility = any(
        (r.risk == "STRICT_ELIGIBILITY" or str(r.risk) == "STRICT_ELIGIBILITY")
        for r in profile.risks
    )

    if has_dsa_signal:
        high_hits += 1
        elite_hits += 1
    if has_multi_rounds:
        high_hits += 1
        elite_hits += 1
    if has_strict_eligibility:
        high_hits += 1

    # BEGINNER is invalid if ANY elite indicator or 2+ high-selectivity signals are present
    if level == DriveDifficultyLevel.beginner.value:
        if elite_hits >= 1:
            logger.error(
                "Difficulty contradiction: BEGINNER classified but elite indicators present. "
                "elite_hits=%d factors=%r", elite_hits, difficulty.difficulty_factors
            )
            raise GovernanceValidationError(
                f"Contradictory difficulty assessment: Drive is classified as BEGINNER but "
                f"elite-level indicators are present in the factors: {difficulty.difficulty_factors}. "
                f"Minimum expected level is COMPETITIVE or higher."
            )
        if high_hits >= 2:
            logger.error(
                "Difficulty contradiction: BEGINNER classified but %d high-selectivity signals found.",
                high_hits,
            )
            raise GovernanceValidationError(
                f"Contradictory difficulty assessment: Drive is classified as BEGINNER but "
                f"{high_hits} high-selectivity factors are present. Minimum expected level is COMPETITIVE."
            )

    # MODERATE is also invalid if 2+ elite indicators are present
    if level == DriveDifficultyLevel.moderate.value:
        if elite_hits >= 2:
            logger.error(
                "Difficulty contradiction: MODERATE classified but %d elite indicators found.",
                elite_hits,
            )
            raise GovernanceValidationError(
                f"Contradictory difficulty assessment: Drive is classified as MODERATE but "
                f"{elite_hits} elite-level indicators are present. Minimum expected level is HIGHLY_COMPETITIVE."
            )

    logger.debug(
        "Difficulty consistency check passed: level=%s high_hits=%d elite_hits=%d",
        level, high_hits, elite_hits,
    )


def _check_relevance_consistency(profile: DriveIntelligenceProfile) -> None:
    """
    Reject placement relevance profiles that mention domains absent from the drive intelligence.

    Specifically:
        - ML/Research/AI profiles are rejected if there are no ML-related competencies or signals.
    """
    relevance = profile.placement_relevance
    if relevance is None:
        return

    # Check if any ML profiles are mentioned
    profile_texts = " ".join(relevance.target_candidate_profiles).lower()
    alignment_texts = " ".join(relevance.project_alignment_areas).lower()
    combined = profile_texts + " " + alignment_texts

    mentions_ml = any(kw in combined for kw in _ML_PROFILE_KEYWORDS)

    if mentions_ml:
        # Verify ML signals exist in the profile
        has_ml_competency = any(
            tc.competency in _ML_COMPETENCIES for tc in profile.technical_competencies
        )
        has_ml_signal = any(
            s.signal in _ML_SIGNALS for s in profile.hiring_signals
        )
        has_ml_technology = any(
            "tensorflow" in t.name.lower()
            or "pytorch" in t.name.lower()
            or "scikit" in t.name.lower()
            or "keras" in t.name.lower()
            or "hugging" in t.name.lower()
            for t in profile.technologies
        )

        if not (has_ml_competency or has_ml_signal or has_ml_technology):
            logger.error(
                "Relevance contradiction: ML profiles mentioned but no ML signals exist in profile. "
                "target_profiles=%r project_areas=%r",
                relevance.target_candidate_profiles,
                relevance.project_alignment_areas,
            )
            raise GovernanceValidationError(
                "Contradictory placement relevance: Drive characterization mentions ML/Research/AI "
                "candidate profiles or project areas, but no ML-related competencies, technologies, "
                "or hiring signals were extracted from the JD. Remove the unsubstantiated ML references."
            )

    logger.debug("Relevance consistency check passed.")


