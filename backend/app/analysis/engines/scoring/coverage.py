from typing import List, Any

def calculate_coverage_score(scored_dimensions: List[Any], expected_count: int) -> float:
    if expected_count == 0:
        return 1.0
        
    verified = 0
    for dim in scored_dimensions:
        if dim:
            # Check if it has an evidence array and it's not empty, or if it's already a scored object with score > 0
            if hasattr(dim, 'evidence') and len(dim.evidence) > 0:
                verified += 1
            elif hasattr(dim, 'score') and dim.score > 0.0:
                verified += 1
                
    return min(1.0, verified / expected_count)
