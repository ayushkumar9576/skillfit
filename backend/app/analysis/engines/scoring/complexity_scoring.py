def calculate_complexity(project_text: str, evidence_count: int) -> float:
    text = project_text.lower()
    score = 0.0
    
    if "architecture" in text or "designed" in text:
        score += 20.0
    if "docker" in text or "kubernetes" in text or "deployed" in text:
        score += 20.0
    if "api" in text and "database" in text:
        score += 20.0
    if "microservices" in text or "distributed" in text:
        score += 30.0
    if "pipeline" in text or "ci/cd" in text:
        score += 15.0
        
    score += min(20.0, evidence_count * 2.0)
    
    return min(100.0, score)
