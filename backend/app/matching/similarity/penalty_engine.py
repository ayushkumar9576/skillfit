from dataclasses import dataclass
from typing import List, Dict, Any
from app.matching.vectorization.canon import normalize_technology_name

@dataclass
class PenaltyResult:
    multiplier: float
    missing_critical_items: List[str]
    missing_count: int

def calculate_penalty(cand_flat: Dict[str, float], drive_payload: Any) -> PenaltyResult:
    """
    Identify drive requirements marked CRITICAL that are not satisfied by the candidate.
    A CRITICAL requirement is explicitly listed in drive_payload.critical_requirements.
    A requirement is missing if the flattened candidate vector has a value of 0.0 (or no key).
    Also checks normalized technology aliases to prevent false-positive gap penalties.
    """
    missing_critical_items = []
    
    for req_key in getattr(drive_payload, "critical_requirements", []):
        cand_val = cand_flat.get(req_key, 0.0)
        
        # Check canonicalized technology alias if direct key lookup yields 0.0
        if cand_val == 0.0 and req_key.startswith("tech:"):
            tech_raw = req_key[5:]
            norm_tech = normalize_technology_name(tech_raw)
            cand_val = cand_flat.get(f"tech:{norm_tech}", 0.0)
            if cand_val == 0.0:
                for k, v in cand_flat.items():
                    if k.startswith("tech:") and normalize_technology_name(k[5:]) == norm_tech and v > 0.0:
                        cand_val = v
                        break
                        
        if cand_val == 0.0:
            missing_critical_items.append(req_key)
                    
    missing_count = len(missing_critical_items)
    
    if missing_count == 0:
        multiplier = 1.00
    elif missing_count == 1:
        multiplier = 0.85
    elif missing_count == 2:
        multiplier = 0.70
    else:
        multiplier = 0.55
        
    return PenaltyResult(
        multiplier=multiplier,
        missing_critical_items=missing_critical_items,
        missing_count=missing_count
    )

