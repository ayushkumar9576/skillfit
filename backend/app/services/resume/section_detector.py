"""
app/services/resume/section_detector.py
---------------------------------------
Section detection engine and strategy hierarchy for SkillFit Phase 3.4.

Provides:
    - BaseSectionDetector (ABC): Abstract interface for section detectors.
    - RuleBasedSectionDetector: Deterministic state machine line scanner.
    - LLMSectionDetector: Extensibility stub for Phase 3.6 LLM Integration Layer.
    - HybridSectionDetector: Extensibility stub for Phase 3.6 Hybrid parser.
    - get_section_detector: Factory function for instantiating detectors.

Design Principles:
    - Pure stateless transformations (text in -> SectionDetectionResult out).
    - Preserves pre-header content under 'contact'.
    - Preserves unmapped content under 'other' (0 text loss).
    - Guarantees all 12 canonical keys are present.
    - Deterministic core coverage confidence calculation.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Set

from app.services.resume.section_headers import match_section_header
from app.services.resume.section_types import (
    DetectionMetrics,
    ResumeSection,
    SectionDetectionResult,
    create_empty_sections,
)

logger = logging.getLogger(__name__)

# Expected core resume sections for student placement evaluation
EXPECTED_CORE_SECTIONS_COUNT: int = 4

# Pattern to identify pure visual divider lines (e.g. '----------------', '================')
DIVIDER_LINE_PATTERN = re.compile(r"^[\=\-\_\*\~\|\#\.\s]{3,}$")


class BaseSectionDetector(ABC):
    """
    Abstract base class for resume section detectors.
    Ensures unified polymorphism across rule-based, LLM, and hybrid detectors.
    """

    @abstractmethod
    def detect_sections(self, text: str) -> SectionDetectionResult:
        """
        Parse raw resume text into structured canonical sections.

        Args:
            text: Plain text extracted from a resume document.

        Returns:
            SectionDetectionResult with canonical sections and parsing metrics.
        """
        pass


class RuleBasedSectionDetector(BaseSectionDetector):
    """
    Deterministic rule-based section detection engine.

    Algorithm:
        1. Ingest raw text and split into sequential lines.
        2. Filter out visual separator lines while tracking non-empty lines.
        3. Maintain an active section state (initialized to ResumeSection.CONTACT).
        4. Detect section headers using match_section_header.
        5. When a header is matched, transition the active section.
        6. Append non-header lines to the active section buffer.
        7. Normalize section strings and compute deterministic coverage metrics.
    """

    def detect_sections(self, text: str) -> SectionDetectionResult:
        """
        Execute deterministic section detection on raw resume text.

        Args:
            text: Raw extracted resume text.

        Returns:
            SectionDetectionResult containing all 12 canonical sections and metrics.
        """
        if not text or not isinstance(text, str) or not text.strip():
            logger.debug("Section detection invoked with empty or invalid text.")
            return SectionDetectionResult(
                sections=create_empty_sections(),
                metrics=DetectionMetrics(
                    total_lines_processed=0,
                    detected_sections_count=0,
                    detected_sections=[],
                    unmapped_lines_count=0,
                    has_contact_info=False,
                    parsing_confidence=0.0,
                ),
            )

        lines: List[str] = text.split("\n")
        section_buffers: Dict[str, List[str]] = {
            section.value: [] for section in ResumeSection
        }

        active_section: ResumeSection = ResumeSection.CONTACT
        detected_sections_set: Set[str] = set()
        total_lines: int = 0
        unmapped_lines: int = 0

        for line in lines:
            stripped = line.strip()

            # Skip empty lines or pure visual dividers
            if not stripped:
                continue

            if DIVIDER_LINE_PATTERN.match(stripped):
                continue

            total_lines += 1

            # Check if this line is a section header
            matched_section = match_section_header(stripped)

            if matched_section is not None:
                # Transition active section to the newly recognized section
                active_section = matched_section
                detected_sections_set.add(matched_section.value)
                logger.debug("Detected section header '%s' -> %s", stripped, matched_section.value)
            else:
                # Append line to the active section's buffer
                section_buffers[active_section.value].append(stripped)
                if active_section == ResumeSection.OTHER:
                    unmapped_lines += 1

        # Post-process buffers into finalized trimmed strings
        final_sections: Dict[str, str] = create_empty_sections()
        for section_name, line_list in section_buffers.items():
            if line_list:
                final_sections[section_name] = "\n".join(line_list).strip()

        # If contact section has non-empty text, record it in detected sections
        has_contact = bool(final_sections[ResumeSection.CONTACT.value])
        if has_contact:
            detected_sections_set.add(ResumeSection.CONTACT.value)

        # -------------------------------------------------------------------
        # Deterministic Core Coverage Confidence Metric
        # -------------------------------------------------------------------
        has_edu = 1 if ResumeSection.EDUCATION.value in detected_sections_set else 0
        has_skills = 1 if ResumeSection.SKILLS.value in detected_sections_set else 0
        has_projects = 1 if ResumeSection.PROJECTS.value in detected_sections_set else 0
        has_exp_or_intern = 1 if (
            ResumeSection.EXPERIENCE.value in detected_sections_set
            or ResumeSection.INTERNSHIPS.value in detected_sections_set
        ) else 0

        core_sections_found = has_edu + has_skills + has_projects + has_exp_or_intern
        confidence = round(
            min(core_sections_found / float(EXPECTED_CORE_SECTIONS_COUNT), 1.0),
            2,
        )

        sorted_detected_sections = sorted(list(detected_sections_set))

        metrics = DetectionMetrics(
            total_lines_processed=total_lines,
            detected_sections_count=len(sorted_detected_sections),
            detected_sections=sorted_detected_sections,
            unmapped_lines_count=unmapped_lines,
            has_contact_info=has_contact,
            parsing_confidence=confidence,
        )

        logger.info(
            "Section detection completed: lines=%d, detected=%d sections, confidence=%.2f",
            total_lines,
            len(sorted_detected_sections),
            confidence,
        )

        return SectionDetectionResult(sections=final_sections, metrics=metrics)


class LLMSectionDetector(BaseSectionDetector):
    """
    Extensibility stub for Phase 3.6 – LLM Integration Layer.
    Will implement AI-powered section disambiguation and parsing fallback.
    """

    def detect_sections(self, text: str) -> SectionDetectionResult:
        raise NotImplementedError(
            "LLM section detection is scheduled for Phase 3.6 (LLM Integration Layer)."
        )


class HybridSectionDetector(BaseSectionDetector):
    """
    Extensibility stub for Phase 3.6 – Hybrid Section Detection.
    Will execute rule-based parsing with LLM fallback on low confidence.
    """

    def detect_sections(self, text: str) -> SectionDetectionResult:
        raise NotImplementedError(
            "Hybrid section detection is scheduled for Phase 3.6 (LLM Integration Layer)."
        )


# ---------------------------------------------------------------------------
# Section Detector Factory
# ---------------------------------------------------------------------------

def get_section_detector(detector_type: str = "rule_based") -> BaseSectionDetector:
    """
    Factory to retrieve an instance of the requested section detector.

    Args:
        detector_type: Type of detector ('rule_based', 'llm', 'hybrid').

    Returns:
        BaseSectionDetector subclass instance.

    Raises:
        ValueError: If an unknown detector type is requested.
    """
    detector_type_lower = (detector_type or "rule_based").lower().strip()

    if detector_type_lower in ("rule_based", "rule", "deterministic"):
        return RuleBasedSectionDetector()
    elif detector_type_lower == "llm":
        return LLMSectionDetector()
    elif detector_type_lower == "hybrid":
        return HybridSectionDetector()
    else:
        raise ValueError(
            f"Unsupported section detector type '{detector_type}'. "
            f"Available types: 'rule_based', 'llm', 'hybrid'."
        )
