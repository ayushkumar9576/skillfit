"""
app/services/resume
-------------------
SkillFit Resume Intelligence Domain Services.

Consolidates all resume-related intelligence processing:
    - Phase 3.4: Resume Section Detection
    - Future Phase 3.5: Analysis Data Models
    - Future Phase 3.6: LLM Integration Layer
    - Future Phases 3.7–3.11: Domain Analysis Engines
"""

from app.services.resume.section_types import (
    CANONICAL_SECTIONS,
    DetectionMetrics,
    ResumeSection,
    SectionDetectionResult,
    create_empty_sections,
)
from app.services.resume.section_headers import (
    MAX_HEADER_CHARS,
    MAX_HEADER_WORDS,
    SECTION_HEADER_MAP,
    match_section_header,
    normalize_header_text,
)
from app.services.resume.section_detector import (
    BaseSectionDetector,
    HybridSectionDetector,
    LLMSectionDetector,
    RuleBasedSectionDetector,
    get_section_detector,
)
from app.services.resume.section_service import (
    detect_sections_for_resume,
    detect_sections_from_text,
)

__all__ = [
    # Types & Models
    "ResumeSection",
    "CANONICAL_SECTIONS",
    "DetectionMetrics",
    "SectionDetectionResult",
    "create_empty_sections",
    # Headers & Normalization
    "MAX_HEADER_CHARS",
    "MAX_HEADER_WORDS",
    "SECTION_HEADER_MAP",
    "normalize_header_text",
    "match_section_header",
    # Detectors & Factory
    "BaseSectionDetector",
    "RuleBasedSectionDetector",
    "LLMSectionDetector",
    "HybridSectionDetector",
    "get_section_detector",
    # Service Functions
    "detect_sections_from_text",
    "detect_sections_for_resume",
]
