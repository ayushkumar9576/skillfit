"""
app/analysis/models/skill_models.py
-----------------------------------
Skill analysis domain models for SkillFit Phase 3.10.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class SkillEvidenceSource:
    """Represents a discrete source providing evidence for a skill."""
    source_type: str
    source_name: str
    source_id: Optional[str]
    source_confidence: float
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class SkillProfile:
    """The unified profile for a single skill extracted from the resume."""
    skill_name: str
    confidence_score: float
    confidence_level: str
    evidence_count: int
    source_count: int
    skill_depth: str
    hiring_signal: str
    evidences: List[SkillEvidenceSource] = field(default_factory=list)


@dataclass
class SkillAnalysisResult:
    """Container for the final, aggregated skills from all upstream engines."""
    skills: List[SkillProfile] = field(default_factory=list)
    total_skills_count: int = 0
