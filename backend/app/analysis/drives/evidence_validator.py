"""
app/analysis/drives/evidence_validator.py
-----------------------------------------
Governance layer evidence validator for Drive Intelligence.

Ensures that LLM-extracted evidence actually exists in the source content,
preventing hallucinated intelligence artifacts.
"""
import logging
import re
from typing import List

from app.analysis.drives.governance import GovernanceValidationError
from app.analysis.drives.schemas.intelligence import DriveIntelligenceProfile, Evidence

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def verify_evidence(profile: DriveIntelligenceProfile, raw_text: str) -> None:
    """
    Verify that all evidence in the profile exists in the raw text.

    Args:
        profile: The extracted DriveIntelligenceProfile.
        raw_text: The normalized text from ParsedDriveContent.

    Raises:
        GovernanceValidationError: If any evidence is hallucinated or too short.
    """
    normalized_raw_text = _normalize_text(raw_text)

    # Collect all evidence from all artifacts
    all_evidence: List[Evidence] = []
    
    if profile.domain:
        all_evidence.extend(profile.domain.evidence)
    
    for tech in profile.technologies:
        all_evidence.extend(tech.evidence)
    for comp in profile.technical_competencies:
        all_evidence.extend(comp.evidence)
    for comp in profile.behavioral_competencies:
        all_evidence.extend(comp.evidence)
    for qual in profile.qualifications:
        all_evidence.extend(qual.evidence)
    for signal in profile.hiring_signals:
        all_evidence.extend(signal.evidence)
    for exp in profile.role_expectations:
        all_evidence.extend(exp.evidence)
    for round_ in profile.selection_process:
        all_evidence.extend(round_.evidence)
    for ind in profile.success_indicators:
        all_evidence.extend(ind.evidence)
    for risk in profile.risks:
        all_evidence.extend(risk.evidence)

    for ev in all_evidence:
        source_text = ev.source_text.strip()
        if len(source_text) < 15:
            logger.error("Evidence too short: %r", source_text)
            raise GovernanceValidationError(f"Evidence text is too short (min 15 chars): '{source_text}'")

        normalized_evidence = _normalize_text(source_text)
        if normalized_evidence not in normalized_raw_text:
            logger.error("Hallucinated evidence detected: %r", source_text)
            raise GovernanceValidationError(f"Hallucinated evidence detected: '{source_text}'")
