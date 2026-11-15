"""
app/analysis/drives/evidence_validator.py
-----------------------------------------
Governance layer evidence validator for Drive Intelligence.

Ensures that LLM-extracted evidence meets minimum structural requirements,
while allowing for inferred intelligence and paraphrasing per the Phase 4 vision.
"""
from typing import Any, List

from pydantic import BaseModel

from app.analysis.drives.governance import GovernanceValidationError
from app.analysis.drives.schemas.intelligence import DriveIntelligenceProfile, Evidence

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
    Verify that every evidence quote is nonempty, including concise JD phrases.
    Exact substring matching has been removed to allow for synthesis and inference.

    Args:
        profile: The extracted DriveIntelligenceProfile.
        raw_text: The normalized text from ParsedDriveContent (kept for API compatibility).

    Raises:
        GovernanceValidationError: If any evidence is blank.
    """
    # Exhaustive recursive collection across all 15+ artifact categories
    all_evidence: List[Evidence] = _collect_all_evidence(profile)

    for ev in all_evidence:
        source_text = ev.source_text.strip()
        if not source_text:
            raise GovernanceValidationError("Evidence quote cannot be blank.")

        # Extraction policing (exact substring matching) has been removed 
        # to fully support inferred intelligence, paraphrasing, and synthesis 
        # according to Phase 4 Vision alignment.
