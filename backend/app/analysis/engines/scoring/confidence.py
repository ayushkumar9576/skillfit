from typing import List
from app.analysis.models.base import AnalysisEvidence, EvidenceType

def get_evidence_quality_weight(evidence_type: str) -> float:
    if evidence_type == EvidenceType.DIRECT_ARCHITECTURE:
        return 0.95
    if evidence_type == EvidenceType.DIRECT_IMPLEMENTATION:
        return 0.90
    if evidence_type == EvidenceType.DIRECT_RESULT:
        return 0.85
    if evidence_type == EvidenceType.CLAIMED:
        return 0.60
    return 0.50

def calculate_confidence(evidence_list: List[AnalysisEvidence], coverage_score: float = 1.0) -> float:
    """
    Confidence reflects evidence certainty, consistency, and quantity.
    """
    if not evidence_list:
        return 0.0
    
    valid_ev = [e for e in evidence_list if e.validated]
    if not valid_ev:
        return 0.0

    max_quality = max(get_evidence_quality_weight(e.evidence_type) for e in valid_ev)
    quantity = len(valid_ev)
    
    quantity_bonus = min(0.2, quantity * 0.05)
    
    base_confidence = min(1.0, max_quality + quantity_bonus)
    
    # Modulate by coverage so confidence reflects how much of the project is evidenced
    coverage_multiplier = 0.5 + (0.5 * coverage_score)
    
    final_conf = base_confidence * coverage_multiplier
    return round(min(1.0, final_conf), 2)
