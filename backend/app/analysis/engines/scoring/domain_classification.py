from typing import Tuple, List

DOMAIN_KEYWORDS = {
    "MACHINE_LEARNING": ["model", "training", "accuracy", "tensorflow", "pytorch", "keras", "scikit-learn", "cnn", "lstm", "neural network"],
    "BACKEND": ["api", "server", "django", "fastapi", "spring", "node.js", "express", "endpoint", "flask"],
    "FRONTEND": ["ui", "ux", "react", "angular", "vue", "css", "html", "interface"],
    "FULL_STACK": ["full stack", "mern", "mean"],
    "MOBILE": ["ios", "android", "flutter", "react native", "swift", "kotlin"],
    "DATA_SCIENCE": ["pandas", "numpy", "matplotlib", "seaborn", "analysis", "dataset"],
    "CLOUD_INFRASTRUCTURE": ["aws", "gcp", "azure", "docker", "kubernetes", "terraform"],
}

def classify_domain(project_text: str) -> Tuple[str, List[str], float]:
    text = project_text.lower()
    scores = {}
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[domain] = score
            
    if not scores:
        return "BACKEND", [], 0.0
        
    sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_domains[0][0]
    secondary = [d[0] for d in sorted_domains[1:3]]
    
    total = sum(scores.values())
    confidence = sorted_domains[0][1] / total if total > 0 else 0.0
    
    return primary, secondary, min(1.0, confidence + 0.3)
