"""
app/matching/vectorization/canon.py
------------------------------------
Canonical dictionary and normalization helpers for technologies and skills.
Ensures semantic aliases (e.g., 'python3' and 'python', 'node.js' and 'nodejs')
resolve to canonical identifiers across candidate and drive vectorization.
"""

from typing import Dict

#: Comprehensive canonical alias mapping for common technologies and variations.
TECHNOLOGY_ALIASES: Dict[str, str] = {
    # Python ecosystem
    "python3": "python",
    "python 3": "python",
    "python3.x": "python",
    "py": "python",
    "fastapi": "fastapi",
    "fast api": "fastapi",
    "flask": "flask",
    "django": "django",
    
    # JavaScript / TypeScript / Node ecosystem
    "node.js": "nodejs",
    "node js": "nodejs",
    "node": "nodejs",
    "nodejs": "nodejs",
    "express.js": "express",
    "expressjs": "express",
    "express js": "express",
    "express": "express",
    "react.js": "react",
    "reactjs": "react",
    "react js": "react",
    "react": "react",
    "next.js": "nextjs",
    "nextjs": "nextjs",
    "next.js14": "nextjs",
    "next 14": "nextjs",
    "next.js 14": "nextjs",
    "vue.js": "vue",
    "vuejs": "vue",
    "vue js": "vue",
    "angular.js": "angular",
    "angularjs": "angular",
    "angular js": "angular",
    "angular": "angular",
    "typescript": "typescript",
    "ts": "typescript",
    "javascript": "javascript",
    "js": "javascript",
    
    # C / C++ / C# / Go / Rust
    "c++": "c++",
    "cpp": "c++",
    "c plus plus": "c++",
    "c#": "c#",
    "csharp": "c#",
    "c sharp": "c#",
    "golang": "go",
    "go lang": "go",
    "rust": "rust",
    
    # Java ecosystem
    "java": "java",
    "spring": "spring",
    "spring boot": "spring boot",
    "springboot": "spring boot",
    
    # Databases & Caching
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "psql": "postgresql",
    "postgre sql": "postgresql",
    "mysql": "mysql",
    "my sql": "mysql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "redis": "redis",
    "sqlite": "sqlite",
    "sqlite3": "sqlite",
    
    # APIs & Protocols
    "rest api": "rest api",
    "restful api": "rest api",
    "rest apis": "rest api",
    "restful apis": "rest api",
    "rest": "rest api",
    "graphql": "graphql",
    "grpc": "grpc",
    
    # DevOps, Cloud & Containers
    "docker": "docker",
    "docker container": "docker",
    "docker containers": "docker",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "azure": "azure",
    "microsoft azure": "azure",
    "git": "git",
    "github": "git",
    "git/github": "git",
    "gitlab": "git",
    
    # Core CS / DSA
    "dsa": "dsa",
    "data structures": "dsa",
    "algorithms": "dsa",
    "data structures and algorithms": "dsa",
    "data structures & algorithms": "dsa",
}

def normalize_technology_name(name: str) -> str:
    """
    Clean, strip, lowercase, and resolve aliases for a technology name.
    
    Example:
        normalize_technology_name("Python3") -> "python"
        normalize_technology_name("Node.js") -> "nodejs"
        normalize_technology_name("PostgreSQL") -> "postgresql"
    """
    cleaned = name.strip().lower()
    return TECHNOLOGY_ALIASES.get(cleaned, cleaned)
