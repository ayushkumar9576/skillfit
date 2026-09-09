"""
app/analysis/drives/evidence_validator.py
-----------------------------------------
Governance layer evidence validator for Drive Intelligence.

Ensures that LLM-extracted evidence actually exists in the source content,
preventing hallucinated intelligence artifacts.
"""
import logging
import re
from typing import Any, List

from pydantic import BaseModel

from app.analysis.drives.governance import GovernanceValidationError
from app.analysis.drives.schemas.intelligence import DriveIntelligenceProfile, Evidence

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _collect_all_evidence(obj: Any) -> List[Evidence]:
    """
    Recursively extract all Evidence instances from any Pydantic model, list, or dict.
    Guarantees no intelligence artifact is missed by validation.
    """
    evidence_list: List[Evidence] = []
    if isinstance(obj, Evidence):
        evidence_list.append(obj)
    elif isinstance(obj, BaseModel):
        for field_name in obj.__class__.model_fields.keys():
            val = getattr(obj, field_name, None)
            if val is not None:
                evidence_list.extend(_collect_all_evidence(val))
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            evidence_list.extend(_collect_all_evidence(item))
    elif isinstance(obj, dict):
        for val in obj.values():
            evidence_list.extend(_collect_all_evidence(val))
    return evidence_list


def verify_evidence(profile: DriveIntelligenceProfile, raw_text: str) -> None:
    """
    Verify that all evidence across all artifacts exists in the raw text.

    Args:
        profile: The extracted DriveIntelligenceProfile.
        raw_text: The normalized text from ParsedDriveContent.

    Raises:
        GovernanceValidationError: If any evidence is hallucinated or too short.
    """
    normalized_raw_text = _normalize_text(raw_text)

    # Exhaustive recursive collection across all 15+ artifact categories
    all_evidence: List[Evidence] = _collect_all_evidence(profile)

    for ev in all_evidence:
        source_text = ev.source_text.strip()
        if len(source_text) < 15:
            logger.error("Evidence too short: %r", source_text)
            raise GovernanceValidationError(f"Evidence text is too short (min 15 chars): '{source_text}'")

        normalized_evidence = _normalize_text(source_text)
        if normalized_evidence not in normalized_raw_text:
            logger.error("Hallucinated evidence detected: %r", source_text)
            raise GovernanceValidationError(f"Hallucinated evidence detected: '{source_text}'")
