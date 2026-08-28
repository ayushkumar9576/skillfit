"""
app/analysis/engines/normalization_engine.py
--------------------------------------------
Provides a centralized technology and skill normalization layer.
Ensures that all downstream databases and matching engines consume
a unified, canonical representation of technical skills.
"""

import re
from typing import Optional

_CANONICAL_SKILLS = {
    # Web Development
    "react": ["reactjs", "react.js", "react js"],
    "next.js": ["nextjs", "next js", "next"],
    "node.js": ["nodejs", "node js", "node"],
    "javascript": ["js", "es6"],
    "typescript": ["ts"],
    
    # Languages
    "python": ["py", "python3", "scripting in python"],
    "c++": ["cpp", "c plus plus", "languages: c++"],
    "java": ["core java", "j2ee"],
    
    # Machine Learning / Data Science
    "scikit-learn": ["sklearn", "sk-learn", "scikit learn"],
    "tensorflow": ["tf", "tensor flow"],
    "pytorch": ["py torch", "torch"],
    "mlflow": ["ml flow"],
    "pandas": ["python pandas"],
    "numpy": ["python numpy"],
    
    # Databases
    "postgresql": ["postgres", "postgre sql"],
    "mongodb": ["mongo", "mongo db"],
    "mysql": ["my sql"],
    
    # Tools & Concepts
    "git": ["github", "git hub", "version control: git"],
    "rest api": ["rest apis", "restful api", "rest", "restful apis"]
}

SKILL_ALIASES = {}
for canonical, aliases in _CANONICAL_SKILLS.items():
    for alias in aliases:
        SKILL_ALIASES[alias] = canonical

INVALID_SKILLS = {
    "", "n/a", "na", "none", "other", "unknown",
    ".", "-", "_", "skill", "skills", "technology", "technologies"
}


def normalize_skill_name(raw_skill: str) -> Optional[str]:
    """
    Normalizes a raw skill/technology string into its canonical form.
    Returns None if the skill is deemed invalid or empty after stripping.
    """
    s = raw_skill.strip().lower()
    # Remove surrounding punctuation
    s = s.strip(".,;:|/\\-_{}[]()")
    # Collapse repeated whitespace
    s = re.sub(r"\s+", " ", s)
    
    if not s or s in INVALID_SKILLS:
        return None
        
    if s in SKILL_ALIASES:
        s = SKILL_ALIASES[s]
        
    return s


def get_display_name(normalized_skill: str) -> str:
    """
    Returns the properly capitalized display name for a normalized skill.
    """
    display_name = normalized_skill.title()
    display_restorations = {
        "node.js": "Node.js",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "next.js": "Next.js",
        "scikit-learn": "Scikit-Learn",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "mlflow": "MLflow",
        "postgresql": "PostgreSQL",
        "mongodb": "MongoDB",
        "mysql": "MySQL",
        "github": "GitHub",
        "api": "API",
        "rest api": "REST API"
    }
    return display_restorations.get(normalized_skill.lower(), display_name)
