from enum import Enum
from typing import List
import re
from app.analysis.models.base import AnalysisEvidence
from app.analysis.models.project_models import DemonstrationLevel

class EvidenceStrength(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

ARCHITECTURE_SIGNALS = ["architected", "designed", "system design", "infrastructure", "topology", "orchestrated", "pipeline"]
IMPLEMENTATION_SIGNALS = ["built", "implemented", "developed", "created", "wrote", "configured", "integrated", "trained", "model"]
USAGE_SIGNALS = ["used", "utilized", "leveraged", "applied", "with", "using"]
MENTION_SIGNALS = ["familiar with", "exposure to", "knowledge of"]

def derive_evidence_strength(evidence_text: str) -> EvidenceStrength:
    text = evidence_text.lower()
    
    if any(sig in text for sig in ARCHITECTURE_SIGNALS):
        return EvidenceStrength.HIGH
    if any(sig in text for sig in IMPLEMENTATION_SIGNALS):
        return EvidenceStrength.HIGH
    if any(sig in text for sig in USAGE_SIGNALS):
        return EvidenceStrength.MEDIUM
    if any(sig in text for sig in MENTION_SIGNALS):
        return EvidenceStrength.LOW
        
    return EvidenceStrength.MEDIUM

def derive_demonstration_level(evidence_list: List[AnalysisEvidence]) -> DemonstrationLevel:
    if not evidence_list:
        return DemonstrationLevel.CLAIMED
        
    combined_text = " ".join([e.evidence_text for e in evidence_list if getattr(e, 'validated', True)]).lower()
    
    if not combined_text:
        return DemonstrationLevel.CLAIMED
        
    if any(sig in combined_text for sig in ARCHITECTURE_SIGNALS):
        return DemonstrationLevel.ARCHITECTED
    if any(sig in combined_text for sig in IMPLEMENTATION_SIGNALS):
        return DemonstrationLevel.IMPLEMENTED
    if any(sig in combined_text for sig in USAGE_SIGNALS):
        return DemonstrationLevel.USED
    if any(sig in combined_text for sig in MENTION_SIGNALS):
        return DemonstrationLevel.MENTIONED
        
    return DemonstrationLevel.CLAIMED

def score_technology(evidence_list: List[AnalysisEvidence], has_results: bool = False) -> float:
    if not evidence_list:
        return 0.0
        
    valid_ev = [e for e in evidence_list if getattr(e, 'validated', True)]
    if not valid_ev:
        return 0.0
        
    level = derive_demonstration_level(valid_ev)
    
    base_scores = {
        DemonstrationLevel.CLAIMED: 40.0,
        DemonstrationLevel.MENTIONED: 50.0,
        DemonstrationLevel.USED: 65.0,
        DemonstrationLevel.IMPLEMENTED: 80.0,
        DemonstrationLevel.ARCHITECTED: 90.0
    }
    
    score = base_scores.get(level, 40.0)
    
    max_strength = max([derive_evidence_strength(e.evidence_text) for e in valid_ev], default=EvidenceStrength.LOW)
    
    if max_strength == EvidenceStrength.HIGH:
        score += 5.0
    elif max_strength == EvidenceStrength.LOW:
        score -= 5.0
        
    quantity = len(valid_ev)
    if quantity > 2:
        score += 3.0
        
    if has_results:
        score += 5.0
        
    return min(100.0, score)
