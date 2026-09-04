"""
app/analysis/drives/consistency_validator.py
--------------------------------------------
Governance layer semantic consistency validator for Drive Intelligence.

Ensures that the LLM has not extracted logically contradictory intelligence,
such as a technology being both required and optional, or conflicting
eligibility criteria.
"""
import logging
from collections import defaultdict

from app.analysis.drives.governance import GovernanceValidationError
from app.analysis.drives.schemas.intelligence import DriveIntelligenceProfile
from app.core.enums import QualificationType

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
    _check_selection_process_contradictions(profile)


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
    Detect conflicting eligibility rules (e.g., Any Branch vs CSE Only).
    """
    branches = []
    backlogs = []

    for qual in profile.qualifications:
        val = qual.expected_value.strip().lower()
        if qual.qualification_type == QualificationType.branch:
            branches.append(val)
        elif qual.qualification_type == QualificationType.backlog_rule:
            backlogs.append(val)

    # 1. Branch contradictions
    if len(branches) > 1:
        has_any = any("any" in b or "all" in b for b in branches)
        has_specific = any("only" in b or ("any" not in b and "all" not in b) for b in branches)
        if has_any and has_specific:
            logger.error("Branch contradiction detected: %r", branches)
            raise GovernanceValidationError(
                f"Contradictory intelligence: Conflicting branch requirements detected: {branches}"
            )

    # 2. Backlog contradictions
    if len(backlogs) > 1:
        # If there are multiple distinct backlog rules extracted, it's highly likely a contradiction
        # since a drive can only have one definitive backlog policy.
        unique_backlogs = set(backlogs)
        if len(unique_backlogs) > 1:
            logger.error("Backlog contradiction detected: %r", unique_backlogs)
            raise GovernanceValidationError(
                f"Contradictory intelligence: Conflicting backlog rules detected: {unique_backlogs}"
            )


def _check_selection_process_contradictions(profile: DriveIntelligenceProfile) -> None:
    """
    Detect structural contradictions in the selection process.
    """
    if not profile.selection_process:
        return
        
    # Check for duplicate step numbers which implies contradictory paths or hallucination
    step_numbers = [round_.step_number for round_ in profile.selection_process]
    if len(step_numbers) != len(set(step_numbers)):
        logger.error("Selection process contradiction: duplicate step numbers %r", step_numbers)
        raise GovernanceValidationError(
            "Contradictory intelligence: Duplicate step numbers in selection process."
        )
