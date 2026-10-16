import math
from typing import Dict

def calculate_cosine_similarity(candidate_vector: Dict[str, float], drive_vector: Dict[str, float]) -> float:
    """
    Calculate the cosine similarity between two sparse vector dictionaries.
    
    Returns a score between 0.0 and 1.0.
    Handles empty vectors and missing dimensions safely.
    """
    if not candidate_vector or not drive_vector:
        return 0.0
        
    # Get the union of all keys
    all_keys = set(candidate_vector.keys()).union(set(drive_vector.keys()))
    
    dot_product = 0.0
    mag_a_sq = 0.0
    mag_b_sq = 0.0
    
    for key in all_keys:
        a_val = candidate_vector.get(key, 0.0)
        b_val = drive_vector.get(key, 0.0)
        
        dot_product += a_val * b_val
        mag_a_sq += a_val * a_val
        mag_b_sq += b_val * b_val
        
    if mag_a_sq == 0.0 or mag_b_sq == 0.0:
        return 0.0
        
    similarity = dot_product / (math.sqrt(mag_a_sq) * math.sqrt(mag_b_sq))
    
    # Ensure precision issues don't push it out of bounds
    return max(0.0, min(1.0, similarity))
