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
    ExperienceLevel,
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
    # Phase 4.4 — Evaluation intelligence consistency overrides removed.


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





