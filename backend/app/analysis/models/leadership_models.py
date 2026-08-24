"""
app/analysis/models/leadership_models.py
----------------------------------------
Positions of responsibility, leadership, and extracurricular domain models for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class PositionOfResponsibilityEvidence:
    """
    Represents a leadership role, club presidency, event coordination, or volunteer post.

    Attributes:
        title: Position title (e.g. 'President, ACM Student Chapter', 'Lead Organizer, HackNIT').
        organization: Institution, club, society, or community organization.
        duration: Timeframe or academic year of holding the position.
        description: Key contributions, initiatives led, or responsibilities executed.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    title: str
    organization: Optional[str] = None
    duration: Optional[str] = None
    description: str = ""
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class PositionOfResponsibilityAnalysisResult:
    """
    Container for all leadership roles and positions of responsibility.

    Attributes:
        positions: List of position of responsibility evidence objects.
        total_positions_count: Total count of leadership roles identified.
    """
    positions: List[PositionOfResponsibilityEvidence] = field(default_factory=list)
    total_positions_count: int = 0
