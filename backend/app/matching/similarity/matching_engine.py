from typing import Any, List
from app.models.candidate_vector import CandidateVectorModel
from app.models.drive_vector import DriveVectorModel
from app.matching.vectorization.schema import (
    CandidateVectorPayload, 
    DriveVectorPayload,
    NAMESPACE_TECH,
    NAMESPACE_COMP,
    NAMESPACE_DOMAIN,
    NAMESPACE_SIGNAL
)
from app.matching.similarity.cosine_similarity import calculate_cosine_similarity
from app.matching.similarity.penalty_engine import calculate_penalty, PenaltyResult
from app.matching.similarity.constants import (
    STRENGTH_CANDIDATE_THRESHOLD,
    STRENGTH_DRIVE_THRESHOLD,
    MAX_STRENGTHS,
    GAP_CANDIDATE_THRESHOLD,
    GAP_DRIVE_THRESHOLD,
    MAX_GAPS,
    GAP_SEVERITY_THRESHOLDS
)
from app.matching.models.scores import MatchScore, DimensionScore
from app.matching.models.result import MatchResult
from app.matching.models.explanation import MatchExplanation, MatchStrength, MatchGap, DimensionBreakdown
from app.matching.enums import MatchDimension, GapSeverity

def _flatten_vector(payload: Any, is_candidate: bool = False) -> dict:
    flat = {}
    
    # Use exact namespace constants to guarantee collision immunity
    mapping = {
        "technologies": NAMESPACE_TECH,
        "competencies": NAMESPACE_COMP,
        "domains": NAMESPACE_DOMAIN,
        "signals": NAMESPACE_SIGNAL
    }
    
    for dim_name, prefix in mapping.items():
        dim_dict = getattr(payload, dim_name, {})
        for k, v in dim_dict.items():
            flat[f"{prefix}{k}"] = v
            
    if is_candidate and hasattr(payload, "project_score"):
        # Not included in cosine sim
        pass
        
    return flat

def match(candidate_vector: CandidateVectorModel, drive_vector: DriveVectorModel) -> MatchResult:
    # 1. Secure parsing
    cand_payload = CandidateVectorPayload(**candidate_vector.vector_json)
    drive_payload = DriveVectorPayload(**drive_vector.vector_json)
    
    # 2. Flatten for Cosine Similarity
    cand_flat = _flatten_vector(cand_payload, is_candidate=True)
    drive_flat = _flatten_vector(drive_payload, is_candidate=False)
    
    # 3. Compute Cosine Similarity
    cosine_sim = calculate_cosine_similarity(cand_flat, drive_flat)
    
    # 4. Penalty Engine (now accepts flat candidate vector and reads metadata)
    penalty: PenaltyResult = calculate_penalty(cand_flat, drive_payload)
    
    # 5. Final Score (Bounded 0 to 1 for models, scaling conceptually mapping to 100)
    final_score = cosine_sim * penalty.multiplier
    final_score = max(0.0, min(1.0, final_score))
    
    # 6. Extract Strengths and Gaps
    strengths: List[MatchStrength] = []
    gaps: List[MatchGap] = []
    
    # We iterate over the flat drive requirements
    for key, d_val in drive_flat.items():
        c_val = cand_flat.get(key, 0.0)
        
        # Instead of parsing the prefix back out, match the exact prefix for dimensionality mapping
        dimension = MatchDimension.TECHNOLOGY # default fallback
        if key.startswith(NAMESPACE_TECH):
            dimension = MatchDimension.TECHNOLOGY
            actual_key = key[len(NAMESPACE_TECH):]
        elif key.startswith(NAMESPACE_COMP):
            dimension = MatchDimension.COMPETENCY
            actual_key = key[len(NAMESPACE_COMP):]
        elif key.startswith(NAMESPACE_DOMAIN):
            dimension = MatchDimension.DOMAIN
            actual_key = key[len(NAMESPACE_DOMAIN):]
        elif key.startswith(NAMESPACE_SIGNAL):
            dimension = MatchDimension.SIGNAL
            actual_key = key[len(NAMESPACE_SIGNAL):]
        else:
            actual_key = key
            
        # Strength Extraction
        if d_val >= STRENGTH_DRIVE_THRESHOLD and c_val >= STRENGTH_CANDIDATE_THRESHOLD:
            impact = (c_val * d_val) # deterministic scoring of strength
            strengths.append(MatchStrength(
                title=f"Strong {actual_key}",
                dimension=dimension,
                description=f"Candidate strongly demonstrates {actual_key}, meeting the drive's expectation.",
                impact_score=max(0.0, min(1.0, impact))
            ))
            
        # Gap Extraction
        if d_val >= GAP_DRIVE_THRESHOLD and c_val <= GAP_CANDIDATE_THRESHOLD:
            # Determine severity
            severity_str = "LOW"
            for thresh, sev in sorted(GAP_SEVERITY_THRESHOLDS.items(), reverse=True):
                if d_val >= thresh:
                    severity_str = sev
                    break
            
            gaps.append(MatchGap(
                title=f"Missing {actual_key}",
                dimension=dimension,
                severity=GapSeverity(severity_str),
                description=f"The drive expects {actual_key} but candidate evidence is weak or missing."
            ))
            
    # Sort and truncate
    strengths.sort(key=lambda x: x.impact_score, reverse=True)
    strengths = strengths[:MAX_STRENGTHS]
    
    # Sort gaps by drive value descending (simulated by severity hierarchy)
    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    gaps.sort(key=lambda x: severity_order.get(x.severity.value, 0), reverse=True)
    gaps = gaps[:MAX_GAPS]
    
    # Generate Deterministic Narrative
    narrative_parts = []
    
    if strengths:
        top_str = [s.title.replace("Strong ", "") for s in strengths[:2]]
        narrative_parts.append(f"Strong alignment in {' and '.join(top_str)}.")
        
    cand_proj = getattr(cand_payload, "project_score", 0.0)
    if cand_proj > 0.8:
        narrative_parts.append("Project sophistication exceeds expectations.")
    elif cand_proj >= 0.5:
        narrative_parts.append("Project sophistication meets general expectations.")
        
    if gaps:
        top_gaps = [g.title.replace("Missing ", "") for g in gaps[:2]]
        if len(top_gaps) == 1:
            narrative_parts.append(f"Missing {top_gaps[0]} experience.")
        else:
            narrative_parts.append(f"Missing {top_gaps[0]} and {top_gaps[1]} experience.")
            
    overall_narrative = " ".join(narrative_parts) if narrative_parts else "No significant strengths or gaps identified."
    
    # 7. Build MatchScore
    # We just put the overall score into the MatchScore. 
    # Dimension scores are omitted for now as this is a flat similarity model.
    match_score = MatchScore(
        overall_score=final_score,
        dimension_scores={},
        coverage_ratio=1.0 if drive_flat else 0.0,
        scoring_version="5.3A"
    )
    
    # 8. Build MatchExplanation
    explanation = MatchExplanation(
        strengths=strengths,
        gaps=gaps,
        dimension_breakdown=[], # Simplified for 5.3A/B
        overall_narrative=overall_narrative
    )
    
    # 9. Return Result
    return MatchResult(
        candidate_id=str(candidate_vector.resume_id),
        drive_id=str(drive_vector.drive_id),
        score=match_score,
        explanation=explanation,
        matching_weights_version="cosine_v1"
    )
