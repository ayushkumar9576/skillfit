"""
app/matching/similarity/matching_engine.py
-------------------------------------------
Production-grade multi-dimensional candidate-to-drive matching engine.
Implements dimensional scoring using MatchingWeights, canonical technology normalization,
domain compatibility mapping, evidence-based hiring signals, project sophistication,
and targeted critical-requirement penalty enforcement.
"""

from typing import Any, List, Dict
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
from app.matching.vectorization.canon import normalize_technology_name
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
from app.matching.models.weights import MatchingWeights
from app.matching.models.scores import MatchScore, DimensionScore
from app.matching.models.result import MatchResult
from app.matching.models.explanation import MatchExplanation, MatchStrength, MatchGap, DimensionBreakdown
from app.matching.enums import MatchDimension, GapSeverity

SCORE_CALIBRATION_CHECKPOINTS = [
    (0.0, 15.0),
    (10.0, 25.0),
    (20.0, 35.0),
    (30.0, 44.0),
    (40.0, 51.0),
    (50.0, 60.0),
    (60.0, 67.0),
    (70.0, 74.0),
    (80.0, 82.0),
    (90.0, 91.0),
    (100.0, 100.0),
]


def adjust_match_score(original_score: float) -> float:
    """
    Adjusts match score (0-100 scale) with a piecewise linear calibration curve
    to provide a confidence and morale boost for candidates.

    Checkpoints:
        [0->15, 10->25, 20->35, 30->44, 40->51, 50->60, 60->67, 70->74, 80->82, 90->91, 100->100]
    """
    if not isinstance(original_score, (int, float)):
        raise TypeError(f"originalScore must be a number, got {type(original_score).__name__!r}.")
    if original_score != original_score:
        raise ValueError("originalScore must not be NaN.")
    if original_score < 0.0 or original_score > 100.0:
        raise ValueError(f"Score must be a number between 0 and 100, got {original_score}.")

    for i in range(len(SCORE_CALIBRATION_CHECKPOINTS) - 1):
        x0, y0 = SCORE_CALIBRATION_CHECKPOINTS[i]
        x1, y1 = SCORE_CALIBRATION_CHECKPOINTS[i + 1]

        if x0 <= original_score <= x1:
            ratio = (original_score - x0) / (x1 - x0)
            adjusted_score = y0 + ratio * (y1 - y0)
            return round(adjusted_score * 10.0) / 10.0

    return original_score

def _flatten_vector(payload: Any, is_candidate: bool = False) -> dict:
    """
    Flatten vector payload into a namespaced dictionary.
    Used for collision-free key lookups, testing, and penalty verification.
    """
    flat = {}
    
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
        # Not included in flat cosine sim
        pass
        
    return flat

def match(candidate_vector: CandidateVectorModel, drive_vector: DriveVectorModel) -> MatchResult:
    # 1. Parse payloads
    cand_payload = CandidateVectorPayload(**candidate_vector.vector_json)
    drive_payload = DriveVectorPayload(**drive_vector.vector_json)
    
    # 2. Flatten for key lookup, namespace safety, and penalty engine
    cand_flat = _flatten_vector(cand_payload, is_candidate=True)
    drive_flat = _flatten_vector(drive_payload, is_candidate=False)
    
    # 3. Determine active dimensions from drive requirements
    weights = MatchingWeights.default()
    active_dimensions: List[MatchDimension] = []
    
    if drive_payload.technologies:
        active_dimensions.append(MatchDimension.TECHNOLOGY)
    if drive_payload.competencies:
        active_dimensions.append(MatchDimension.COMPETENCY)
    if drive_payload.domains:
        active_dimensions.append(MatchDimension.DOMAIN)
    if drive_payload.signals:
        active_dimensions.append(MatchDimension.SIGNAL)
        if any(k in drive_payload.signals for k in ["STRONG_PROJECTS", "PROJECT_FOCUSED"]):
            active_dimensions.append(MatchDimension.PROJECT)
            
    # For full drives with core technical requirements, include project and behavioral dimensions
    if len(active_dimensions) >= 3 and MatchDimension.PROJECT not in active_dimensions:
        active_dimensions.append(MatchDimension.PROJECT)
    if len(active_dimensions) >= 4 and MatchDimension.BEHAVIORAL not in active_dimensions:
        active_dimensions.append(MatchDimension.BEHAVIORAL)
        
    if not active_dimensions:
        return MatchResult(
            candidate_id=str(candidate_vector.resume_id),
            drive_id=str(drive_vector.drive_id),
            score=MatchScore.zero(),
            explanation=MatchExplanation(),
            matching_weights_version=weights.version
        )
        
    # 4. Compute per-dimension raw scores, items, and reasoning
    raw_scores: Dict[MatchDimension, float] = {}
    matched_counts: Dict[MatchDimension, int] = {}
    total_counts: Dict[MatchDimension, int] = {}
    reasonings: Dict[MatchDimension, str] = {}
    
    # --- Dimension: TECHNOLOGY ---
    if MatchDimension.TECHNOLOGY in active_dimensions:
        cand_techs = cand_payload.technologies
        drive_techs = drive_payload.technologies
        tech_sim = calculate_cosine_similarity(cand_techs, drive_techs)
        t_matched = sum(1 for k in drive_techs if cand_techs.get(k, 0.0) >= 0.2 or cand_techs.get(normalize_technology_name(k), 0.0) >= 0.2)
        t_total = len(drive_techs)
        
        raw_scores[MatchDimension.TECHNOLOGY] = tech_sim
        matched_counts[MatchDimension.TECHNOLOGY] = t_matched
        total_counts[MatchDimension.TECHNOLOGY] = t_total
        reasonings[MatchDimension.TECHNOLOGY] = f"Matched {t_matched}/{t_total} drive technologies with {tech_sim*100:.1f}% similarity."
        
    # --- Dimension: COMPETENCY ---
    if MatchDimension.COMPETENCY in active_dimensions:
        cand_comps = cand_payload.competencies
        drive_comps = drive_payload.competencies
        comp_sim = calculate_cosine_similarity(cand_comps, drive_comps)
        c_matched = sum(1 for k in drive_comps if cand_comps.get(k, 0.0) >= 0.2)
        c_total = len(drive_comps)
        
        raw_scores[MatchDimension.COMPETENCY] = comp_sim
        matched_counts[MatchDimension.COMPETENCY] = c_matched
        total_counts[MatchDimension.COMPETENCY] = c_total
        reasonings[MatchDimension.COMPETENCY] = f"Demonstrated {c_matched}/{c_total} core competencies with {comp_sim*100:.1f}% alignment."
        
    # --- Dimension: DOMAIN ---
    if MatchDimension.DOMAIN in active_dimensions:
        cand_doms = cand_payload.domains
        drive_doms = drive_payload.domains
        d_total = len(drive_doms)
        d_matched = 0
        dom_dot = 0.0
        
        sw_subdomains = {"BACKEND", "FRONTEND", "FULL_STACK", "DISTRIBUTED_SYSTEMS", "SOFTWARE_ARCHITECTURE", "MOBILE", "DEVOPS", "CLOUD"}
        for dk, dv in drive_doms.items():
            if dk in cand_doms:
                dom_dot += dv * cand_doms[dk]
                d_matched += 1
            elif dk == "SOFTWARE_ENGINEERING" and any(sd in cand_doms for sd in sw_subdomains):
                dom_dot += dv * 1.0
                d_matched += 1
            elif dk == "DATA" and any(sd in cand_doms for sd in ["DATA_SCIENCE", "DATA_ENGINEERING"]):
                dom_dot += dv * 1.0
                d_matched += 1
            elif dk == "AI_ML" and any(sd in cand_doms for sd in ["MACHINE_LEARNING", "DEEP_LEARNING", "MLOPS"]):
                dom_dot += dv * 1.0
                d_matched += 1
                
        dom_sim = dom_dot / sum(drive_doms.values()) if drive_doms else 1.0
        dom_sim = max(0.0, min(1.0, dom_sim))
        
        raw_scores[MatchDimension.DOMAIN] = dom_sim
        matched_counts[MatchDimension.DOMAIN] = d_matched
        total_counts[MatchDimension.DOMAIN] = d_total
        reasonings[MatchDimension.DOMAIN] = f"Domain alignment score {dom_sim*100:.1f}% for {list(drive_doms.keys())}."
        
    # --- Dimension: SIGNAL ---
    if MatchDimension.SIGNAL in active_dimensions:
        cand_sigs = cand_payload.signals
        drive_sigs = drive_payload.signals
        sig_sim = calculate_cosine_similarity(cand_sigs, drive_sigs)
        s_matched = sum(1 for k in drive_sigs if cand_sigs.get(k, 0.0) >= 0.2)
        s_total = len(drive_sigs)
        
        raw_scores[MatchDimension.SIGNAL] = sig_sim
        matched_counts[MatchDimension.SIGNAL] = s_matched
        total_counts[MatchDimension.SIGNAL] = s_total
        reasonings[MatchDimension.SIGNAL] = f"Aligned with {s_matched}/{s_total} hiring signals and success indicators ({sig_sim*100:.1f}%)."
        
    # --- Dimension: PROJECT ---
    if MatchDimension.PROJECT in active_dimensions:
        cand_proj = getattr(cand_payload, "project_score", 0.0)
        p_matched = 1 if cand_proj >= 0.5 else 0
        
        raw_scores[MatchDimension.PROJECT] = cand_proj
        matched_counts[MatchDimension.PROJECT] = p_matched
        total_counts[MatchDimension.PROJECT] = 1
        reasonings[MatchDimension.PROJECT] = f"Project sophistication score of {cand_proj*100:.1f}%."
        
    # --- Dimension: BEHAVIORAL ---
    if MatchDimension.BEHAVIORAL in active_dimensions:
        cand_sigs = cand_payload.signals
        if any(k in cand_sigs for k in ["OWNED", "LED", "ARCHITECTURE"]):
            beh_score = 0.85
            b_matched = 1
            b_reason = "Demonstrated strong ownership, leadership, and engineering architecture practices."
        elif any(k in cand_sigs for k in ["CONTRIBUTED", "IMPLEMENTED", "TESTING"]):
            beh_score = 0.75
            b_matched = 1
            b_reason = "Demonstrated implementation ownership, testing discipline, and team contribution."
        else:
            beh_score = 0.50
            b_matched = 0
            b_reason = "Baseline behavioral and teamwork expectations."
            
        raw_scores[MatchDimension.BEHAVIORAL] = beh_score
        matched_counts[MatchDimension.BEHAVIORAL] = b_matched
        total_counts[MatchDimension.BEHAVIORAL] = 1
        reasonings[MatchDimension.BEHAVIORAL] = b_reason
        
    # 5. Weight Normalization & DimensionScore Construction
    active_weight_sum = sum(weights.get_weight(d) for d in active_dimensions)
    dimension_scores: Dict[str, DimensionScore] = {}
    weighted_scores: Dict[MatchDimension, float] = {}
    base_score = 0.0
    
    for dim in active_dimensions:
        raw_w = weights.get_weight(dim)
        norm_w = raw_w / active_weight_sum
        raw_sc = raw_scores[dim]
        w_sc = raw_sc * norm_w
        weighted_scores[dim] = w_sc
        base_score += w_sc
        
        dimension_scores[dim.value] = DimensionScore(
            dimension=dim,
            raw_score=max(0.0, min(1.0, raw_sc)),
            weight=raw_w,
            weighted_score=max(0.0, min(1.0, w_sc)),
            matched_items=matched_counts[dim],
            total_items=total_counts[dim],
            reasoning=reasonings[dim]
        )
        
    # 6. Penalty Engine Calculation
    penalty: PenaltyResult = calculate_penalty(cand_flat, drive_payload)
    raw_final_score = base_score * penalty.multiplier
    raw_final_score = max(0.0, min(1.0, raw_final_score))
    
    # 6b. Morale Boost Score Adjustment (Piecewise linear calibration curve)
    boosted_pct = adjust_match_score(raw_final_score * 100.0)
    boosted_final_score = max(0.0, min(1.0, boosted_pct / 100.0))
    
    # 7. Extract Strengths and Gaps
    strengths: List[MatchStrength] = []
    gaps: List[MatchGap] = []
    
    for key, d_val in drive_flat.items():
        c_val = cand_flat.get(key, 0.0)
        
        dimension = MatchDimension.TECHNOLOGY
        if key.startswith(NAMESPACE_TECH):
            dimension = MatchDimension.TECHNOLOGY
            actual_key = key[len(NAMESPACE_TECH):]
            if c_val == 0.0:
                c_val = cand_flat.get(f"tech:{normalize_technology_name(actual_key)}", 0.0)
        elif key.startswith(NAMESPACE_COMP):
            dimension = MatchDimension.COMPETENCY
            actual_key = key[len(NAMESPACE_COMP):]
        elif key.startswith(NAMESPACE_DOMAIN):
            dimension = MatchDimension.DOMAIN
            actual_key = key[len(NAMESPACE_DOMAIN):]
            if c_val == 0.0 and actual_key == "SOFTWARE_ENGINEERING":
                if any(cand_flat.get(f"domain:{sd}", 0.0) > 0 for sd in ["BACKEND", "FRONTEND", "FULL_STACK"]):
                    c_val = 1.0
        elif key.startswith(NAMESPACE_SIGNAL):
            dimension = MatchDimension.SIGNAL
            actual_key = key[len(NAMESPACE_SIGNAL):]
        else:
            actual_key = key
            
        # Strength Extraction
        if d_val >= STRENGTH_DRIVE_THRESHOLD and c_val >= STRENGTH_CANDIDATE_THRESHOLD:
            impact = (c_val * d_val)
            strengths.append(MatchStrength(
                title=f"Strong {actual_key}",
                dimension=dimension,
                description=f"Candidate strongly demonstrates {actual_key}, meeting the drive's expectation.",
                impact_score=max(0.0, min(1.0, impact))
            ))
            
        # Gap Extraction
        if d_val >= GAP_DRIVE_THRESHOLD and c_val <= GAP_CANDIDATE_THRESHOLD:
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
    
    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    gaps.sort(key=lambda x: severity_order.get(x.severity.value, 0), reverse=True)
    gaps = gaps[:MAX_GAPS]
    
    # 8. Build DimensionBreakdown
    dimension_breakdown: List[DimensionBreakdown] = []
    for dim in active_dimensions:
        dim_strengths = [s for s in strengths if s.dimension == dim]
        dim_gaps = [g for g in gaps if g.dimension == dim]
        dimension_breakdown.append(DimensionBreakdown(
            dimension=dim,
            raw_score=max(0.0, min(1.0, raw_scores[dim])),
            weighted_score=max(0.0, min(1.0, weighted_scores[dim])),
            strengths=dim_strengths,
            gaps=dim_gaps,
            narrative=reasonings[dim]
        ))
        
    # 9. Deterministic Narrative Construction
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
    
    # 10. Build MatchScore & MatchExplanation
    match_score = MatchScore(
        overall_score=boosted_final_score,
        dimension_scores=dimension_scores,
        coverage_ratio=len(active_dimensions) / 6.0,
        scoring_version="5.3.0",
        raw_score=raw_final_score,
    )
    
    explanation = MatchExplanation(
        strengths=strengths,
        gaps=gaps,
        dimension_breakdown=dimension_breakdown,
        overall_narrative=overall_narrative
    )
    
    return MatchResult(
        candidate_id=str(candidate_vector.resume_id),
        drive_id=str(drive_vector.drive_id),
        score=match_score,
        explanation=explanation,
        matching_weights_version=weights.version
    )
