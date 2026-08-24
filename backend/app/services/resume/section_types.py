"""
app/services/resume/section_types.py
------------------------------------
Centralized domain section definitions, data structures, and metrics
for SkillFit Phase 3.4 – Resume Section Detection.

Supported Canonical Sections (12):
    - contact
    - summary
    - education
    - skills
    - projects
    - internships
    - experience
    - certifications
    - achievements
    - positions_of_responsibility
    - publications
    - other

Design Rules:
    - Pure internal domain models (@dataclass, standard Enum).
    - No API serialization / FastAPI dependencies.
    - Missing sections are represented as empty strings (""), never None.
    - All canonical keys are guaranteed to be present in output dictionaries.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


class ResumeSection(str, Enum):
    """
    Canonical enumeration of supported resume sections in SkillFit.
    These canonical names are strictly maintained across all analysis engines.
    """
    CONTACT = "contact"
    SUMMARY = "summary"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    INTERNSHIPS = "internships"
    EXPERIENCE = "experience"
    CERTIFICATIONS = "certifications"
    ACHIEVEMENTS = "achievements"
    POSITIONS_OF_RESPONSIBILITY = "positions_of_responsibility"
    PUBLICATIONS = "publications"
    OTHER = "other"


# Immutable tuple of canonical section names in standardized order
CANONICAL_SECTIONS: tuple[str, ...] = tuple(section.value for section in ResumeSection)


def create_empty_sections() -> Dict[str, str]:
    """
    Generate a canonical section dictionary where all 12 supported sections
    are initialized with empty strings ("").

    Returns:
        Dict[str, str]: Dictionary containing every canonical section key.
    """
    return {section.value: "" for section in ResumeSection}


@dataclass
class DetectionMetrics:
    """
    Deterministic parsing statistics and confidence metrics for resume section detection.

    Attributes:
        total_lines_processed: Total count of non-empty and processed lines in the resume.
        detected_sections_count: Number of unique non-empty sections detected.
        detected_sections: Alphabetically sorted list of detected canonical section names.
        unmapped_lines_count: Number of content lines routed to 'other' or unrecognized.
        has_contact_info: Boolean indicating whether contact information was identified.
        parsing_confidence: Deterministic core-coverage confidence score (0.0 to 1.0).
    """
    total_lines_processed: int = 0
    detected_sections_count: int = 0
    detected_sections: List[str] = field(default_factory=list)
    unmapped_lines_count: int = 0
    has_contact_info: bool = False
    parsing_confidence: float = 0.0


@dataclass
class SectionDetectionResult:
    """
    Encapsulates the complete result of section detection for a resume.

    Attributes:
        sections: Canonical dictionary of all 12 sections mapping to their string contents.
        metrics: Deterministic parsing and coverage statistics.
    """
    sections: Dict[str, str] = field(default_factory=create_empty_sections)
    metrics: DetectionMetrics = field(default_factory=DetectionMetrics)
