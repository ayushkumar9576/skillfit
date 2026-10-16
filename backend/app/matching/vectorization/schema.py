import dataclasses
from typing import Dict, Any, List

VECTOR_SCHEMA_VERSION = 1

# Namespaces to prevent feature collision
NAMESPACE_TECH = "tech:"
NAMESPACE_COMP = "comp:"
NAMESPACE_DOMAIN = "domain:"
NAMESPACE_SIGNAL = "signal:"

@dataclasses.dataclass
class CandidateVectorPayload:
    schema_version: int
    technologies: Dict[str, float]
    competencies: Dict[str, float]
    domains: Dict[str, float]
    signals: Dict[str, float]
    project_score: float = 0.0

    def __post_init__(self):
        if self.schema_version != VECTOR_SCHEMA_VERSION:
            raise ValueError(f"Invalid schema version: {self.schema_version}")
        if not (0.0 <= self.project_score <= 1.0):
            raise ValueError("project_score must be between 0.0 and 1.0")

@dataclasses.dataclass
class DriveVectorPayload:
    schema_version: int
    technologies: Dict[str, float]
    competencies: Dict[str, float]
    domains: Dict[str, float]
    signals: Dict[str, float]
    critical_requirements: List[str] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        if self.schema_version != VECTOR_SCHEMA_VERSION:
            raise ValueError(f"Invalid schema version: {self.schema_version}")
