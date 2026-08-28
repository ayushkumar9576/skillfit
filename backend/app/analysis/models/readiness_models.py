"""
app/analysis/models/readiness_models.py
---------------------------------------
Readiness Engine domain models for SkillFit Phase 3.11.

Provides 100% deterministic, rule-based data structures for the 
candidate placement readiness evaluation.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List


class ReadinessLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AnalysisStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


DEPTH_ADVANCED = "ADVANCED"
DEPTH_INTERMEDIATE = "INTERMEDIATE"
DEPTH_BEGINNER = "BEGINNER"


# Centralized Hiring Signal Mapping
HIRING_SIGNAL_WEIGHTS = {
    "HIGH": 100.0,
    "MEDIUM": 70.0,
    "LOW": 40.0,
}


@dataclass
class ReadinessStrength:
    title: str
    evidence_count: int
    reasoning: str
    impact_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "evidence_count": self.evidence_count,
            "reasoning": self.reasoning,
            "impact_score": self.impact_score,
        }


@dataclass
class ReadinessGap:
    title: str
    severity: Severity
    reasoning: str

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "severity": self.severity.value,
            "reasoning": self.reasoning,
        }


@dataclass
class ScoreBreakdown:
    project_score: float
    internship_score: float
    certification_score: float
    skill_score: float
    project_contributors: dict = None

    def to_dict(self) -> dict:
        return {
            "project_score": self.project_score,
            "internship_score": self.internship_score,
            "certification_score": self.certification_score,
            "skill_score": self.skill_score,
            "project_contributors": self.project_contributors or {},
        }


@dataclass
class ReadinessAnalysisResult:
    resume_id: str
    engine_version: str
    analysis_status: AnalysisStatus
    
    readiness_score: float
    readiness_level: ReadinessLevel
    overall_confidence: float

    score_breakdown: ScoreBreakdown

    strengths: List[ReadinessStrength]
    gaps: List[ReadinessGap]

    advanced_skill_count: int
    intermediate_skill_count: int
    beginner_skill_count: int
    high_signal_skill_count: int
    medium_signal_skill_count: int
    low_signal_skill_count: int
    
    project_count: int
    internship_count: int
    certification_count: int
    skill_count: int
    evidence_count: int

    generated_at: datetime

    def to_dict(self) -> dict:
        return {
            "resume_id": self.resume_id,
            "engine_version": self.engine_version,
            "analysis_status": self.analysis_status.value,
            "readiness_score": self.readiness_score,
            "readiness_level": self.readiness_level.value,
            "overall_confidence": self.overall_confidence,
            "score_breakdown": self.score_breakdown.to_dict(),
            "strengths": [s.to_dict() for s in self.strengths],
            "gaps": [g.to_dict() for g in self.gaps],
            "advanced_skill_count": self.advanced_skill_count,
            "intermediate_skill_count": self.intermediate_skill_count,
            "beginner_skill_count": self.beginner_skill_count,
            "high_signal_skill_count": self.high_signal_skill_count,
            "medium_signal_skill_count": self.medium_signal_skill_count,
            "low_signal_skill_count": self.low_signal_skill_count,
            "project_count": self.project_count,
            "internship_count": self.internship_count,
            "certification_count": self.certification_count,
            "skill_count": self.skill_count,
            "evidence_count": self.evidence_count,
            "generated_at": self.generated_at.isoformat(),
        }
