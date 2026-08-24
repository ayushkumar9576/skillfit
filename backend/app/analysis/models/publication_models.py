"""
app/analysis/models/publication_models.py
-----------------------------------------
Academic publications, research papers, and patent domain models for SkillFit Phase 3.5.

Consumed by:
    - Phase 3.11: Readiness Engine
    - Phase 3.12: Analysis Persistence
    - Phase 3.13: Public CV APIs
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.analysis.models.base import AnalysisEvidence


@dataclass
class PublicationEvidence:
    """
    Represents an academic paper, journal article, conference proceeding, or patent.

    Attributes:
        title: Title of the published paper or patent.
        publisher: Journal, conference, or patent authority (e.g. 'IEEE Access', 'Springer').
        publication_date: Date or year of publication.
        url: Link to DOI or published paper if available.
        description: Abstract or summary of findings and novel contributions.
        authors: List of co-authors as stated in the document.
        confidence: Extraction confidence score (0.0 to 1.0).
        evidences: List of supporting resume textual statements.
    """
    title: str
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    url: Optional[str] = None
    description: str = ""
    authors: List[str] = field(default_factory=list)
    confidence: float = 1.0
    evidences: List[AnalysisEvidence] = field(default_factory=list)


@dataclass
class PublicationAnalysisResult:
    """
    Container for all research publications and patents extracted from a resume.

    Attributes:
        publications: List of publication evidence objects.
        total_publications_count: Total count of published works identified.
    """
    publications: List[PublicationEvidence] = field(default_factory=list)
    total_publications_count: int = 0
